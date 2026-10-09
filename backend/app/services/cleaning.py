import gc
import logging
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.dataset import Dataset
from app.services.cloud_storage import supabase_storage
from app.services.dataset_storage import (
    build_cloud_storage_id,
    cleanup_dataset_local_path,
    get_cloud_storage_id,
    get_dataset_local_path,
    is_cloud_dataset,
)
from app.utils.files import create_temporary_file_path

logger = logging.getLogger(__name__)


# Keep CSV cleaning bounded on Render Free (512 MB RAM). Excel files retain
# the existing path because pandas' Excel readers do not support chunking.
LARGE_CSV_BYTES = 80 * 1024 * 1024
# Smaller chunks reduce peak memory on Render's 512 MB Free instance.
CLEANING_CHUNK_ROWS = 1_000


def _clean_large_csv(
    dataset: Dataset,
    file_path: Path,
    *,
    apply: bool,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Preview or clean a large CSV one chunk at a time.

    Duplicate fingerprints are tracked in a temporary SQLite database, not
    a Python set, so memory use stays bounded even when there are many rows.
    Median/mode filling and IQR outlier detection are performed per chunk;
    this is a memory-safe approximation for very large files.
    """
    summary: dict[str, Any] = {
        "rows_before": 0,
        "rows_after": 0,
        "columns": 0,
        "empty_strings_replaced": 0,
        "whitespace_cleaned": 0,
        "missing_values_before": 0,
        "missing_values_after": 0,
        "missing_values_filled": 0,
        "duplicates_removed": 0,
        "outliers_detected": {},
        "changes": [],
        "warnings": [
            "Large CSV memory-safe mode processes chunks independently; "
            "median/mode replacements and outlier thresholds are estimated "
            "per chunk rather than globally."
        ],
        "memory_safe_chunked": True,
        "chunk_rows": CLEANING_CHUNK_ROWS,
    }

    seen_path = create_temporary_file_path(
        prefix="insightforge_clean_seen_",
        suffix=".sqlite3",
    )
    connection: sqlite3.Connection | None = None
    first_chunk = True

    try:
        connection = sqlite3.connect(str(seen_path))
        connection.execute("PRAGMA journal_mode=OFF")
        connection.execute("PRAGMA synchronous=OFF")
        connection.execute(
            "CREATE TABLE seen_rows (fingerprint TEXT PRIMARY KEY)"
        )
        if apply:
            if output_path is None:
                raise ValueError("output_path is required when applying cleaning")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.unlink(missing_ok=True)

        for chunk in pd.read_csv(
            file_path,
            chunksize=CLEANING_CHUNK_ROWS,
            low_memory=True,
        ):
            summary["rows_before"] += len(chunk)
            summary["columns"] = len(chunk.columns)
            summary["missing_values_before"] += int(chunk.isna().sum().sum())

            cleaned, part = _clean_dataframe(chunk, copy=False)
            del chunk

            # Deduplicate across chunk boundaries using a disk-backed index.
            # Hash and deduplicate one small chunk at a time. Keep only the
            # compact fingerprints and boolean mask for this chunk in RAM.
            fingerprints = pd.util.hash_pandas_object(
                cleaned,
                index=False,
            ).to_numpy(dtype="uint64", copy=False)
            keep_mask: list[bool] = []
            for fingerprint in fingerprints:
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO seen_rows(fingerprint) VALUES (?)",
                    (str(int(fingerprint)),),
                )
                keep_mask.append(cursor.rowcount == 1)
            connection.commit()

            duplicates = len(keep_mask) - sum(keep_mask)
            if duplicates:
                cleaned = cleaned.loc[keep_mask].reset_index(drop=True)
            summary["duplicates_removed"] += (
                part["duplicates_removed"] + duplicates
            )
            summary["rows_after"] += len(cleaned)
            summary["empty_strings_replaced"] += part["empty_strings_replaced"]
            summary["whitespace_cleaned"] += part["whitespace_cleaned"]
            summary["missing_values_filled"] += part["missing_values_filled"]
            summary["missing_values_after"] += int(cleaned.isna().sum().sum())

            for column, count in part["outliers_detected"].items():
                summary["outliers_detected"][column] = (
                    summary["outliers_detected"].get(column, 0) + count
                )

            for change in part["changes"]:
                key = (change.get("column"), change.get("action"))
                existing = next(
                    (item for item in summary["changes"]
                     if (item.get("column"), item.get("action")) == key),
                    None,
                )
                if existing is None:
                    summary["changes"].append(dict(change))
                else:
                    existing["count"] = existing.get("count", 0) + change.get("count", 0)
                    if "replacement_value" in change:
                        existing["replacement_value"] = change["replacement_value"]

            if apply:
                cleaned.to_csv(
                    output_path,
                    mode="w" if first_chunk else "a",
                    header=first_chunk,
                    index=False,
                )
                first_chunk = False

            del cleaned, part, fingerprints, keep_mask
            gc.collect()

        if summary["rows_before"] == 0:
            raise ValueError("Dataset is empty.")
        if summary["duplicates_removed"]:
            summary["changes"].append({
                "column": None,
                "action": "duplicate_rows_removed",
                "count": summary["duplicates_removed"],
            })
        summary["missing_values_filled"] = max(
            0,
            summary["missing_values_before"] - summary["missing_values_after"],
        )
        return summary
    finally:
        if connection is not None:
            connection.close()
        seen_path.unlink(missing_ok=True)
        gc.collect()


def load_dataset_file(
    dataset: Dataset,
) -> tuple[pd.DataFrame, Path, bool]:
    """
    Load a dataset into a pandas DataFrame.

    Returns:
        (dataframe, local_path, temporary)

    For local datasets:
        temporary = False

    For Supabase datasets:
        the dataset is reconstructed into a temporary local file.
    """

    try:
        file_path, temporary = get_dataset_local_path(
            dataset.file_path
        )
    except (
        FileNotFoundError,
        ValueError,
        RuntimeError,
    ):
        logger.warning(
            "Dataset source file is unavailable "
            "(dataset_id=%s).",
            dataset.id,
        )

        raise HTTPException(
            status_code=404,
            detail="Dataset file not found on server.",
        ) from None

    try:
        if dataset.file_type.lower() == "csv":
            dataframe = pd.read_csv(file_path)

        elif dataset.file_type.lower() in {
            "xlsx",
            "xls",
        }:
            dataframe = pd.read_excel(file_path)

        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported dataset file type.",
            )

        return dataframe, file_path, temporary

    except HTTPException:
        cleanup_dataset_local_path(
            file_path,
            temporary,
        )
        raise

    except Exception:
        logger.exception(
            "Failed to load dataset for cleaning"
        )

        cleanup_dataset_local_path(
            file_path,
            temporary,
        )

        raise HTTPException(
            status_code=400,
            detail="Unable to read dataset.",
        ) from None


def _clean_dataframe(
    df: pd.DataFrame,
    *,
    copy: bool = True,
    preview_only: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Apply safe automatic cleaning operations.

    Cleaning rules:
    - Empty/whitespace-only strings -> missing
    - Leading/trailing whitespace -> removed
    - Numeric missing values -> median
    - Non-numeric missing values -> mode
    - Duplicate rows -> removed
    - Outliers -> detected only, never automatically removed

    ``copy=False`` lets read-only callers (the preview endpoint) skip a
    full duplicate of the frame, which matters for multi-hundred-megabyte
    uploads on memory-constrained hosts.
    """

    cleaned = df.copy() if copy else df

    summary: dict[str, Any] = {
        "rows_before": len(df),
        "rows_after": len(df),
        "columns": len(df.columns),
        "empty_strings_replaced": 0,
        "whitespace_cleaned": 0,
        "missing_values_before": int(
            df.isna().sum().sum()
        ),
        "missing_values_after": 0,
        "missing_values_filled": 0,
        "duplicates_removed": 0,
        "outliers_detected": {},
        "changes": [],
        "warnings": [],
    }

    # ============================================================
    # 1. CLEAN STRING VALUES
    # ============================================================

    string_columns = cleaned.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in string_columns:
        original = cleaned[column].copy()

        cleaned[column] = cleaned[column].apply(
            lambda value: value.strip()
            if isinstance(value, str)
            else value
        )

        whitespace_changed = int(
            (
                original.fillna("__NA__").astype(str)
                != cleaned[column]
                .fillna("__NA__")
                .astype(str)
            ).sum()
        )

        if whitespace_changed:
            summary["whitespace_cleaned"] += (
                whitespace_changed
            )

        empty_mask = cleaned[column].apply(
            lambda value: (
                isinstance(value, str)
                and value.strip() == ""
            )
        )

        empty_count = int(
            empty_mask.sum()
        )

        if empty_count:
            cleaned.loc[
                empty_mask,
                column,
            ] = np.nan

            summary[
                "empty_strings_replaced"
            ] += empty_count

            summary["changes"].append(
                {
                    "column": str(column),
                    "action": (
                        "empty_strings_to_missing"
                    ),
                    "count": empty_count,
                }
            )

    # ============================================================
    # 2. REMOVE DUPLICATES
    # ============================================================

    duplicate_count = int(
        cleaned.duplicated(
            keep="first"
        ).sum()
    )

    if duplicate_count:
        cleaned = (
            cleaned
            .drop_duplicates(
                keep="first"
            )
            .reset_index(drop=True)
        )

        summary[
            "duplicates_removed"
        ] = duplicate_count

        summary["changes"].append(
            {
                "column": None,
                "action": (
                    "duplicate_rows_removed"
                ),
                "count": duplicate_count,
            }
        )

    # ============================================================
    # 3. FILL MISSING NUMERIC VALUES
    # ============================================================

    numeric_columns = cleaned.select_dtypes(
        include=["number"]
    ).columns

    for column in numeric_columns:
        missing_count = int(
            cleaned[column].isna().sum()
        )

        if missing_count == 0:
            continue

        median = cleaned[column].median()

        if pd.isna(median):
            summary["warnings"].append(
                f"Column '{column}' contains missing "
                "numeric values but has no usable median."
            )
            continue

        if not preview_only:
            cleaned[column] = (
                cleaned[column].fillna(median)
            )

        summary[
            "missing_values_filled"
        ] += missing_count

        summary["changes"].append(
            {
                "column": str(column),
                "action": (
                    "missing_numeric_filled_with_median"
                ),
                "count": missing_count,
                "replacement_value": float(
                    median
                ),
            }
        )

    # ============================================================
    # 4. FILL MISSING NON-NUMERIC VALUES
    # ============================================================

    non_numeric_columns = cleaned.select_dtypes(
        exclude=["number"]
    ).columns

    for column in non_numeric_columns:
        missing_count = int(
            cleaned[column].isna().sum()
        )

        if missing_count == 0:
            continue

        mode = cleaned[column].mode(
            dropna=True
        )

        if mode.empty:
            summary["warnings"].append(
                f"Column '{column}' contains missing "
                "values but has no usable mode."
            )
            continue

        replacement = mode.iloc[0]

        if not preview_only:
            cleaned[column] = (
                cleaned[column].fillna(
                    replacement
                )
            )

        summary[
            "missing_values_filled"
        ] += missing_count

        summary["changes"].append(
            {
                "column": str(column),
                "action": (
                    "missing_values_filled_with_mode"
                ),
                "count": missing_count,
                "replacement_value": str(
                    replacement
                ),
            }
        )

    # ============================================================
    # 5. OUTLIER DETECTION
    # ============================================================

    for column in numeric_columns:
        series = cleaned[column].dropna()

        if series.empty:
            summary[
                "outliers_detected"
            ][str(column)] = 0
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        if iqr == 0:
            count = 0
        else:
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            count = int(
                (
                    (series < lower)
                    | (series > upper)
                ).sum()
            )

        summary[
            "outliers_detected"
        ][str(column)] = count

    # ============================================================
    # 6. FINAL COUNTS
    # ============================================================

    summary["rows_after"] = len(cleaned)

    if preview_only:
        # Preview mode does not need to materialize filled columns.
        # Derive the final missing count from the values that can be
        # safely filled instead of allocating another full-frame scan.
        summary["missing_values_after"] = max(
            0,
            summary["missing_values_before"]
            - summary["missing_values_filled"],
        )
    else:
        summary[
            "missing_values_after"
        ] = int(
            cleaned.isna().sum().sum()
        )

        summary[
            "missing_values_filled"
        ] = (
            summary["missing_values_before"]
            - summary["missing_values_after"]
        )

    return cleaned, summary


def preview_cleaning(
    dataset: Dataset,
) -> dict[str, Any]:
    """
    Generate a cleaning preview without modifying
    or creating any files.
    """

    try:
        local_path, temporary = get_dataset_local_path(dataset.file_path)
    except (FileNotFoundError, ValueError, RuntimeError):
        raise HTTPException(status_code=404, detail="Dataset file not found on server.") from None

    try:
        if (
            dataset.file_type.lower() == "csv"
            and local_path.stat().st_size > LARGE_CSV_BYTES
        ):
            summary = _clean_large_csv(dataset, local_path, apply=False)
        else:
            if dataset.file_type.lower() == "csv":
                df = pd.read_csv(local_path)
            elif dataset.file_type.lower() in {"xlsx", "xls"}:
                df = pd.read_excel(local_path)
            else:
                raise HTTPException(status_code=400, detail="Unsupported dataset file type.")
            try:
                _, summary = _clean_dataframe(df, copy=False, preview_only=True)
            finally:
                del df
                gc.collect()

        return {
            "dataset_id": dataset.id,
            "original_filename": dataset.original_filename,
            "file_type": dataset.file_type,
            "preview": summary,
        }
    finally:
        cleanup_dataset_local_path(local_path, temporary)


def _cleaned_extension(
    dataset: Dataset,
) -> str:
    """
    Return the output extension for a cleaned dataset.
    """

    extension = dataset.file_type.lower()

    if extension == "xls":
        return ".xlsx"

    return f".{extension}"


def _cleaned_filename(
    dataset: Dataset,
) -> str:
    """
    Build a stable human-readable cleaned filename.
    """

    original_name = Path(
        dataset.original_filename
    ).name

    stem = Path(
        original_name
    ).stem

    return (
        f"{stem}_cleaned"
        f"{_cleaned_extension(dataset)}"
    )


def _local_cleaned_path(
    dataset: Dataset,
    original_path: Path,
) -> Path:
    """
    Return the path for a local cleaned dataset based on the
    user-facing original filename, not the randomized storage name.
    """

    return (
        original_path.parent
        / _cleaned_filename(dataset)
    )


def _build_cleaned_storage_id(
    dataset: Dataset,
) -> str:
    """
    Build the Supabase storage identifier for a cleaned file.
    """

    return build_cloud_storage_id(
        f"{dataset.id}/cleaned"
    )


def apply_cleaning(
    dataset: Dataset,
) -> dict[str, Any]:
    """
    Apply cleaning and save the result separately.

    The original dataset is never modified.

    With cloud storage enabled:
        - original is downloaded temporarily
        - cleaned file is created temporarily
        - cleaned file is uploaded to Supabase
        - temporary files are deleted

    With cloud storage disabled:
        - existing local behavior is preserved.
    """

    try:
        original_path, original_temporary = get_dataset_local_path(dataset.file_path)
    except (FileNotFoundError, ValueError, RuntimeError):
        raise HTTPException(status_code=404, detail="Dataset file not found on server.") from None

    cleaned_path: Path | None = None
    df: pd.DataFrame | None = None
    cleaned_df: pd.DataFrame | None = None

    try:
        cleaned_filename = _cleaned_filename(dataset)
        output_extension = _cleaned_extension(dataset)
        is_large_csv = (
            dataset.file_type.lower() == "csv"
            and original_path.stat().st_size > LARGE_CSV_BYTES
        )

        if is_large_csv:
            if is_cloud_dataset(dataset.file_path):
                cleaned_path = create_temporary_file_path(
                    prefix="insightforge_cleaned_",
                    suffix=".csv",
                )
            else:
                cleaned_path = _local_cleaned_path(dataset, original_path)
            summary = _clean_large_csv(
                dataset,
                original_path,
                apply=True,
                output_path=cleaned_path,
            )
            cleaned_df = None
        else:
            if dataset.file_type.lower() == "csv":
                df = pd.read_csv(original_path)
            elif dataset.file_type.lower() in {"xlsx", "xls"}:
                df = pd.read_excel(original_path)
            else:
                raise HTTPException(status_code=400, detail="Unsupported dataset file type.")
            cleaned_df, summary = _clean_dataframe(df)

        # --------------------------------------------------------
        # Local storage mode
        # --------------------------------------------------------

        if not is_cloud_dataset(
            dataset.file_path
        ):
            cleaned_path = _local_cleaned_path(
                dataset,
                original_path,
            )

            try:
                if cleaned_df is not None:
                    if output_extension == ".csv":
                        cleaned_df.to_csv(cleaned_path, index=False)
                    else:
                        cleaned_df.to_excel(cleaned_path, index=False)

            except Exception:
                logger.exception(
                    "Failed to save cleaned dataset"
                )

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Unable to save cleaned dataset."
                    ),
                ) from None

            summary[
                "cleaned_filename"
            ] = cleaned_filename

            summary[
                "cleaned_file_path"
            ] = str(cleaned_path)

            return {
                "dataset_id": dataset.id,
                "original_filename": (
                    dataset.original_filename
                ),
                "cleaned_filename": (
                    cleaned_filename
                ),
                "download_available": True,
                "preview": summary,
            }

        # --------------------------------------------------------
        # Supabase storage mode
        # --------------------------------------------------------

        if cleaned_path is None:
            cleaned_path = create_temporary_file_path(
                prefix="insightforge_cleaned_",
                suffix=output_extension,
            )

        try:
            if cleaned_df is not None:
                if output_extension == ".csv":
                    cleaned_df.to_csv(cleaned_path, index=False)
                else:
                    cleaned_df.to_excel(cleaned_path, index=False)

            cleaned_storage_id = (
                _build_cleaned_storage_id(
                    dataset
                )
            )

            supabase_storage.upload_file(
                cleaned_path,
                cleaned_storage_id,
            )

            summary[
                "cleaned_filename"
            ] = cleaned_filename

            summary[
                "cleaned_file_path"
            ] = cleaned_storage_id

            return {
                "dataset_id": dataset.id,
                "original_filename": (
                    dataset.original_filename
                ),
                "cleaned_filename": (
                    cleaned_filename
                ),
                "download_available": True,
                "preview": summary,
            }

        finally:
            cleaned_path.unlink(
                missing_ok=True
            )
            cleaned_path = None

    finally:
        if df is not None:
            del df
        if cleaned_df is not None:
            del cleaned_df
        gc.collect()
        if cleaned_path is not None and is_cloud_dataset(dataset.file_path):
            cleaned_path.unlink(missing_ok=True)
        cleanup_dataset_local_path(original_path, original_temporary)


def get_cleaned_file_path(
    dataset: Dataset,
) -> Path:
    """
    Return a local path for the cleaned dataset.

    For local datasets:
        returns the existing local cleaned file.

    For Supabase datasets:
        downloads the cleaned file to a temporary
        local path.

    The caller is responsible for deleting the returned
    temporary path when the response has completed.
    """

    # ------------------------------------------------------------
    # Local dataset
    # ------------------------------------------------------------

    if not is_cloud_dataset(
        dataset.file_path
    ):
        original_path, _ = (
            get_dataset_local_path(
                dataset.file_path
            )
        )

        cleaned_path = _local_cleaned_path(
            dataset,
            original_path,
        )

        if not cleaned_path.exists():
            raise HTTPException(
                status_code=404,
                detail=(
                    "Cleaned dataset has not "
                    "been generated yet."
                ),
            )

        return cleaned_path

    # ------------------------------------------------------------
    # Supabase dataset
    # ------------------------------------------------------------

    cleaned_storage_id = (
        _build_cleaned_storage_id(
            dataset
        )
    )

    path = create_temporary_file_path(
        prefix="insightforge_cleaned_download_",
        suffix=_cleaned_extension(dataset),
    )

    try:
        supabase_storage.download_file(
            cleaned_storage_id,
            path,
        )

        return path

    except Exception:
        path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=404,
            detail=(
                "Cleaned dataset has not "
                "been generated yet."
            ),
        ) from None
