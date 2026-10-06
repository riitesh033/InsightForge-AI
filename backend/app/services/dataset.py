import logging
import shutil
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.services.cloud_storage import supabase_storage
from app.services.dataset_storage import (
    build_cloud_storage_id,
    create_local_dataset_path,
    dataset_storage_root,
)
from app.services.entitlements import (
    enforce_dataset_count,
    enforce_upload_size,
    lock_user_for_quota,
)
from app.services.insights import (
    calculate_quality_score_details,
    generate_dataset_summary,
)
from app.services.profiling import profile_dataframe
from app.services.professional_analysis import (
    generate_professional_analysis,
)

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls",
}


def make_json_serializable(obj):
    """
    Recursively convert pandas/numpy objects into JSON-safe values.
    """

    if isinstance(obj, dict):
        return {
            k: make_json_serializable(v)
            for k, v in obj.items()
        }

    if isinstance(obj, list):
        return [
            make_json_serializable(v)
            for v in obj
        ]

    if isinstance(obj, tuple):
        return tuple(
            make_json_serializable(v)
            for v in obj
        )

    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()

    if isinstance(obj, pd.Timedelta):
        return str(obj)

    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        return float(obj)

    if isinstance(obj, np.bool_):
        return bool(obj)

    if pd.isna(obj):
        return None

    return obj


def upload_dataset(
    db: Session,
    file: UploadFile,
    owner_id: int,
):
    """
    Upload, profile, analyze, and persist a dataset.

    When USE_CLOUD_STORAGE is False:
        The existing local filesystem workflow is used.

    When USE_CLOUD_STORAGE is True:
        The uploaded dataset is temporarily stored locally,
        uploaded to Supabase Storage, and the database stores
        only a short Supabase storage identifier.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )

    original_filename = Path(
        file.filename.replace("\\", "/")
    ).name

    extension = Path(
        original_filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only CSV, XLSX and XLS files are supported."
            ),
        )

    lock_user_for_quota(
        db,
        owner_id,
    )

    enforce_dataset_count(
        db,
        owner_id,
    )

    # ------------------------------------------------------------
    # Determine upload size
    # ------------------------------------------------------------

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    enforce_upload_size(
        db,
        owner_id,
        file_size,
    )

    unique_filename = (
        f"{uuid4().hex}{extension}"
    )

    # ------------------------------------------------------------
    # Save the upload locally first.
    #
    # This local copy is temporary when cloud storage is enabled.
    # Pandas needs a local file for profiling/analysis.
    # ------------------------------------------------------------

    storage_root = dataset_storage_root()
    storage_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    save_path = create_local_dataset_path(
        unique_filename
    )

    cloud_storage_id: str | None = None
    cloud_uploaded = False

    try:
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer,
            )

        # --------------------------------------------------------
        # Read the dataset
        # --------------------------------------------------------

        try:
            if extension == ".csv":
                dataframe = pd.read_csv(
                    save_path
                )
            else:
                dataframe = pd.read_excel(
                    save_path
                )

        except Exception:
            logger.exception(
                "Failed to read uploaded dataset"
            )

            raise HTTPException(
                status_code=400,
                detail="Unable to read dataset.",
            ) from None

        # --------------------------------------------------------
        # Generate deterministic analysis
        # --------------------------------------------------------

        try:
            analysis_data = profile_dataframe(
                dataframe
            )

            analysis_data = make_json_serializable(
                analysis_data
            )

            professional_analysis = (
                generate_professional_analysis(
                    dataframe
                )
            )

            analysis_text = generate_dataset_summary(
                analysis_data
            )

            quality_score_details = (
                calculate_quality_score_details(
                    analysis_data
                )
            )

            quality_score = (
                quality_score_details["score"]
            )

            analysis_data["summary"][
                "quality_score"
            ] = quality_score

            analysis_data["summary"][
                "quality_score_factors"
            ] = quality_score_details[
                "factors"
            ]

        except Exception:
            logger.exception(
                "Failed to profile uploaded dataset"
            )

            raise HTTPException(
                status_code=500,
                detail="Unable to profile dataset.",
            ) from None

        # --------------------------------------------------------
        # Create database objects
        #
        # We flush first so dataset.id is available.
        # The ID is then used to create the stable Supabase
        # storage identifier.
        # --------------------------------------------------------

        dataset = Dataset(
            filename=unique_filename,
            original_filename=original_filename,
            file_type=extension.replace(
                ".",
                "",
            ),
            file_size=file_size,
            file_path=unique_filename,
            rows=len(dataframe),
            columns=len(dataframe.columns),
            owner_id=owner_id,
        )

        analysis = Analysis(
            dataset=dataset,
            summary=analysis_data[
                "summary"
            ],
            summary_text=analysis_text,
            quality_score=quality_score,
            column_info=analysis_data[
                "column_info"
            ],
            statistics=analysis_data[
                "statistics"
            ],
            missing_values=analysis_data[
                "missing_values"
            ],
            duplicates=analysis_data[
                "duplicates"
            ],
            correlations=analysis_data[
                "correlations"
            ],
            outliers=analysis_data[
                "outliers"
            ],
            executive_summary=(
                professional_analysis.get(
                    "executive_summary"
                )
            ),
            key_insights=(
                professional_analysis.get(
                    "key_insights"
                )
            ),
            recommendations=(
                professional_analysis.get(
                    "recommendations"
                )
            ),
            business_opportunities=(
                professional_analysis.get(
                    "business_opportunities"
                )
            ),
            distributions=(
                professional_analysis.get(
                    "distributions"
                )
            ),
            data_quality_issues=(
                professional_analysis
                .get("data_quality", {})
                .get("issues")
            ),
        )

        db.add(dataset)
        db.add(analysis)

        # Make dataset.id available.
        db.flush()

        # --------------------------------------------------------
        # Cloud storage
        # --------------------------------------------------------

        if settings.USE_CLOUD_STORAGE:
            if not supabase_storage.is_configured():
                raise RuntimeError(
                    "Cloud storage is enabled but "
                    "Supabase Storage is not configured."
                )

            cloud_storage_id = (
                build_cloud_storage_id(
                    dataset.id
                )
            )

            supabase_storage.upload_file(
                save_path,
                cloud_storage_id,
            )

            cloud_uploaded = True

            dataset.file_path = cloud_storage_id

        # --------------------------------------------------------
        # Local storage
        # --------------------------------------------------------

        else:
            dataset.file_path = unique_filename

        # --------------------------------------------------------
        # Persist everything
        # --------------------------------------------------------

        db.commit()
        db.refresh(dataset)

        return dataset

    except HTTPException:
        db.rollback()

        if cloud_uploaded and cloud_storage_id:
            supabase_storage.delete_file(
                cloud_storage_id
            )

        save_path.unlink(
            missing_ok=True
        )

        raise

    except Exception:
        db.rollback()

        if cloud_uploaded and cloud_storage_id:
            supabase_storage.delete_file(
                cloud_storage_id
            )

        save_path.unlink(
            missing_ok=True
        )

        logger.exception(
            "Failed to persist uploaded dataset "
            "and analysis"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to save dataset.",
        ) from None