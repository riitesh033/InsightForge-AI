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
        value = float(obj)

        if not np.isfinite(value):
            return None

        return value

    if isinstance(obj, np.bool_):
        return bool(obj)

    try:
        if pd.isna(obj):
            return None
    except (TypeError, ValueError):
        pass

    return obj


def upload_dataset(
    db: Session,
    file: UploadFile,
    owner_id: int,
):
    """
    Upload, persist, profile, and analyze a dataset.

    Cloud-storage workflow:

        Browser
            ↓
        Temporary local file
            ↓
        Supabase Storage
            ↓
        Database dataset record
            ↓
        Pandas profiling / professional analysis
            ↓
        Database analysis record

    The important difference from the previous implementation is
    that the durable Supabase copy is created BEFORE the expensive
    analysis work starts.
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
    # Temporary local storage
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
        # --------------------------------------------------------
        # Save the incoming upload locally.
        # --------------------------------------------------------

        logger.info(
            "Saving uploaded dataset locally: %s",
            original_filename,
        )

        with save_path.open("wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer,
            )

        logger.info(
            "Temporary dataset saved: %s bytes",
            file_size,
        )

        # --------------------------------------------------------
        # IMPORTANT:
        # Upload to Supabase BEFORE expensive analysis.
        #
        # We use a UUID-based storage ID here rather than the
        # database ID because the database ID does not exist yet.
        # --------------------------------------------------------

        if settings.USE_CLOUD_STORAGE:
            if not supabase_storage.is_configured():
                raise RuntimeError(
                    "Cloud storage is enabled but "
                    "Supabase Storage is not configured."
                )

            cloud_storage_id = (
                f"supabase:datasets/uploads/"
                f"{uuid4().hex}"
            )

            logger.info(
                "Uploading dataset to Supabase: %s",
                cloud_storage_id,
            )

            supabase_storage.upload_file(
                save_path,
                cloud_storage_id,
            )

            cloud_uploaded = True

            logger.info(
                "Dataset successfully uploaded to Supabase: %s",
                cloud_storage_id,
            )

        # --------------------------------------------------------
        # Read the dataset
        # --------------------------------------------------------

        logger.info(
            "Reading dataset with pandas: %s",
            original_filename,
        )

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

        logger.info(
            "Dataset loaded: rows=%s columns=%s",
            len(dataframe),
            len(dataframe.columns),
        )

        # --------------------------------------------------------
        # Generate deterministic analysis
        # --------------------------------------------------------

        try:
            logger.info(
                "Starting dataset profiling."
            )

            analysis_data = profile_dataframe(
                dataframe
            )

            analysis_data = make_json_serializable(
                analysis_data
            )

            logger.info(
                "Starting professional dataset analysis."
            )

            professional_analysis = (
                generate_professional_analysis(
                    dataframe
                )
            )

            professional_analysis = make_json_serializable(
                professional_analysis
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
        # --------------------------------------------------------

        dataset_file_path = (
            cloud_storage_id
            if cloud_storage_id
            else unique_filename
        )

        dataset = Dataset(
            filename=unique_filename,
            original_filename=original_filename,
            file_type=extension.replace(
                ".",
                "",
            ),
            file_size=file_size,
            file_path=dataset_file_path,
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
                .get(
                    "data_quality",
                    {},
                )
                .get(
                    "issues"
                )
            ),
        )

        db.add(dataset)
        db.add(analysis)

        db.commit()
        db.refresh(dataset)

        logger.info(
            "Dataset upload completed successfully: "
            "dataset_id=%s filename=%s",
            dataset.id,
            original_filename,
        )

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