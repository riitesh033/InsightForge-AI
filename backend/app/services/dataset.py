import gc
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

# Render's free web service has 512 MB RAM. A large CSV can easily exceed
# that when pandas materializes the whole file and the analysis pipeline
# creates additional temporary DataFrames. Keep expensive analysis bounded
# for large CSVs while still scanning the complete file in small chunks.
LARGE_CSV_BYTES = 80 * 1024 * 1024
ANALYSIS_SAMPLE_ROWS = 25_000
ANALYSIS_CHUNK_ROWS = 10_000


def _read_dataset_for_analysis(
    save_path: Path,
    extension: str,
) -> tuple[pd.DataFrame, int, bool]:
    """Load a dataset without materializing a large CSV in RAM.

    Returns the DataFrame used for analysis, the exact dataset row count, and
    whether the analysis DataFrame is a bounded sample. Small datasets keep
    the existing full-data behavior. Large CSVs are parsed in chunks and only
    the first bounded sample is retained for the expensive analysis steps.
    """

    if extension != ".csv" or save_path.stat().st_size <= LARGE_CSV_BYTES:
        dataframe = (
            pd.read_csv(save_path)
            if extension == ".csv"
            else pd.read_excel(save_path)
        )
        return dataframe, len(dataframe), False

    logger.info(
        "Large CSV detected (%s bytes); using chunked analysis with "
        "a %s-row bounded sample.",
        save_path.stat().st_size,
        ANALYSIS_SAMPLE_ROWS,
    )

    sample_parts: list[pd.DataFrame] = []
    sample_rows = 0
    total_rows = 0

    try:
        for chunk in pd.read_csv(
            save_path,
            chunksize=ANALYSIS_CHUNK_ROWS,
            low_memory=True,
        ):
            total_rows += len(chunk)

            if sample_rows < ANALYSIS_SAMPLE_ROWS:
                take = min(
                    ANALYSIS_SAMPLE_ROWS - sample_rows,
                    len(chunk),
                )
                if take:
                    sample_parts.append(
                        chunk.iloc[:take].copy()
                    )
                    sample_rows += take

            # Release each parsed chunk as soon as it has been accounted for.
            del chunk

        if not sample_parts:
            raise ValueError("Dataset is empty.")

        dataframe = pd.concat(
            sample_parts,
            ignore_index=True,
        )
        del sample_parts
        gc.collect()

        return dataframe, total_rows, True

    except Exception:
        logger.exception(
            "Failed to read large CSV in bounded chunks."
        )
        raise


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
    existing_cloud_storage_id: str | None = None,
):
    """
    Persist, profile, and analyze a dataset.

    Normal upload workflow:

        Browser
            ↓
        Render
            ↓
        Temporary local file
            ↓
        Supabase Storage
            ↓
        Database dataset record
            ↓
        Pandas analysis

    Chunked cloud upload workflow:

        Browser
            ↓
        Supabase Storage chunks
            ↓
        Render temporary reconstructed file
            ↓
        Database dataset record
            ↓
        Pandas analysis

    When existing_cloud_storage_id is provided, the file has
    already been uploaded to Supabase and must not be uploaded
    again.
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

    # Cloud storage is engaged when the deployment enables it, and always
    # when the caller already uploaded the bytes to Supabase (the chunked
    # browser flow). In that second case the data genuinely lives in
    # Supabase, so the database record must reference it there: a
    # local-only record would lose the dataset on the next container
    # restart, which is exactly the failure this project must not have.
    use_cloud_storage = bool(
        settings.USE_CLOUD_STORAGE or existing_cloud_storage_id
    )

    cloud_storage_id: str | None = None

    cloud_uploaded = False

    if use_cloud_storage and existing_cloud_storage_id:
        cloud_storage_id = existing_cloud_storage_id

    try:
        # --------------------------------------------------------
        # Save the reconstructed/incoming upload locally.
        # --------------------------------------------------------

        logger.info(
            "Saving dataset locally: %s",
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
        # Upload to Supabase only when the caller has not already
        # uploaded the file there.
        # --------------------------------------------------------

        if use_cloud_storage:
            if not supabase_storage.is_configured():
                raise RuntimeError(
                    "Cloud storage is enabled but "
                    "Supabase Storage is not configured."
                )

            if existing_cloud_storage_id:
                if not existing_cloud_storage_id.startswith(
                    "supabase:"
                ):
                    raise ValueError(
                        "Invalid existing cloud storage ID."
                    )

                cloud_storage_id = (
                    existing_cloud_storage_id
                )

                logger.info(
                    "Using existing Supabase dataset: %s",
                    cloud_storage_id,
                )

            else:
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
            "Reading dataset with a memory-safe analysis loader: %s",
            original_filename,
        )

        try:
            dataframe, dataset_row_count, analysis_sampled = (
                _read_dataset_for_analysis(
                    save_path,
                    extension,
                )
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
            "Dataset loaded for analysis: rows=%s columns=%s sampled=%s",
            dataset_row_count,
            len(dataframe.columns),
            analysis_sampled,
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

            # Preserve the exact dataset size even when large CSV analysis
            # uses a bounded sample to stay below Render's memory limit.
            analysis_data["summary"]["rows"] = dataset_row_count
            analysis_data["summary"]["columns"] = len(dataframe.columns)
            analysis_data["summary"]["analysis_sampled"] = analysis_sampled
            if analysis_sampled:
                analysis_data["summary"]["analysis_sample_rows"] = len(dataframe)

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
            rows=dataset_row_count,
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

        # The analysis objects are now JSON-safe Python values. Release the
        # bounded DataFrame before committing so the peak memory does not
        # overlap unnecessarily with the ORM transaction.
        del dataframe
        gc.collect()

        db.commit()
        db.refresh(dataset)

        logger.info(
            "Dataset upload completed successfully: "
            "dataset_id=%s filename=%s",
            dataset.id,
            original_filename,
        )

        # A cloud-backed dataset is served from Supabase, so the local
        # staging copy is redundant. Leaving it behind would slowly fill
        # the host filesystem without ever being read again.
        if cloud_storage_id:
            save_path.unlink(
                missing_ok=True
            )

        return dataset

    except HTTPException:
        db.rollback()

        # Delete from Supabase only when this function itself
        # created the cloud upload.
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

        # Delete from Supabase only when this function itself
        # created the cloud upload.
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
