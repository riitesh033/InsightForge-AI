from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.models.dataset import Dataset


def load_dataset_file(dataset: Dataset) -> pd.DataFrame:
    """
    Load a dataset using the same storage information used by the
    existing dataset upload/download system.
    """

    file_path = Path(dataset.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Dataset file not found on server.",
        )

    try:
        if dataset.file_type.lower() == "csv":
            return pd.read_csv(file_path)

        if dataset.file_type.lower() in {"xlsx", "xls"}:
            return pd.read_excel(file_path)

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to read dataset: {str(exc)}",
        )

    raise HTTPException(
        status_code=400,
        detail="Unsupported dataset file type.",
    )


def _clean_dataframe(
    df: pd.DataFrame,
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
    """

    cleaned = df.copy()

    summary: dict[str, Any] = {
        "rows_before": len(df),
        "rows_after": len(df),
        "columns": len(df.columns),
        "empty_strings_replaced": 0,
        "whitespace_cleaned": 0,
        "missing_values_before": int(df.isna().sum().sum()),
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

        # Strip leading/trailing whitespace.
        cleaned[column] = cleaned[column].apply(
            lambda value: value.strip()
            if isinstance(value, str)
            else value
        )

        whitespace_changed = int(
            (
                original.fillna("__NA__").astype(str)
                != cleaned[column].fillna("__NA__").astype(str)
            ).sum()
        )

        if whitespace_changed:
            summary["whitespace_cleaned"] += whitespace_changed

        # Empty strings become missing values.
        empty_mask = cleaned[column].apply(
            lambda value: isinstance(value, str)
            and value.strip() == ""
        )

        empty_count = int(empty_mask.sum())

        if empty_count:
            cleaned.loc[empty_mask, column] = np.nan

            summary["empty_strings_replaced"] += empty_count

            summary["changes"].append(
                {
                    "column": str(column),
                    "action": "empty_strings_to_missing",
                    "count": empty_count,
                }
            )

    # ============================================================
    # 2. REMOVE DUPLICATES
    # ============================================================

    duplicate_count = int(
        cleaned.duplicated(keep="first").sum()
    )

    if duplicate_count:
        cleaned = cleaned.drop_duplicates(
            keep="first"
        ).reset_index(drop=True)

        summary["duplicates_removed"] = duplicate_count

        summary["changes"].append(
            {
                "column": None,
                "action": "duplicate_rows_removed",
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

        # Median is safer than mean when outliers exist.
        median = cleaned[column].median()

        if pd.isna(median):
            summary["warnings"].append(
                f"Column '{column}' contains missing numeric "
                "values but has no usable median."
            )
            continue

        cleaned[column] = cleaned[column].fillna(median)

        summary["missing_values_filled"] += missing_count

        summary["changes"].append(
            {
                "column": str(column),
                "action": "missing_numeric_filled_with_median",
                "count": missing_count,
                "replacement_value": float(median),
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

        mode = cleaned[column].mode(dropna=True)

        if mode.empty:
            summary["warnings"].append(
                f"Column '{column}' contains missing values "
                "but has no usable mode."
            )
            continue

        replacement = mode.iloc[0]

        cleaned[column] = cleaned[column].fillna(
            replacement
        )

        summary["missing_values_filled"] += missing_count

        summary["changes"].append(
            {
                "column": str(column),
                "action": "missing_values_filled_with_mode",
                "count": missing_count,
                "replacement_value": str(replacement),
            }
        )

    # ============================================================
    # 5. OUTLIER DETECTION
    # ============================================================

    for column in numeric_columns:
        series = cleaned[column].dropna()

        if series.empty:
            summary["outliers_detected"][str(column)] = 0
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

        summary["outliers_detected"][str(column)] = count

    # ============================================================
    # 6. FINAL COUNTS
    # ============================================================

    summary["rows_after"] = len(cleaned)

    summary["missing_values_after"] = int(
        cleaned.isna().sum().sum()
    )

    summary["missing_values_filled"] = (
        summary["missing_values_before"]
        - summary["missing_values_after"]
    )

    return cleaned, summary


def preview_cleaning(
    dataset: Dataset,
) -> dict[str, Any]:
    """
    Generate a cleaning preview without modifying or creating
    any files.
    """

    df = load_dataset_file(dataset)

    _, summary = _clean_dataframe(df)

    return {
        "dataset_id": dataset.id,
        "original_filename": dataset.original_filename,
        "file_type": dataset.file_type,
        "preview": summary,
    }


def apply_cleaning(
    dataset: Dataset,
) -> dict[str, Any]:
    """
    Apply cleaning and save the result as a separate file.

    The original dataset is never modified.
    """

    df = load_dataset_file(dataset)

    cleaned_df, summary = _clean_dataframe(df)

    original_path = Path(dataset.file_path)

    extension = dataset.file_type.lower()

    # XLS cannot reliably be written by pandas without additional
    # legacy Excel writers, so convert cleaned XLS files to XLSX.
    if extension == "xls":
        output_extension = ".xlsx"
    else:
        output_extension = f".{extension}"

    cleaned_filename = (
        f"{original_path.stem}_cleaned{output_extension}"
    )

    cleaned_path = (
        original_path.parent / cleaned_filename
    )

    try:
        if output_extension == ".csv":
            cleaned_df.to_csv(
                cleaned_path,
                index=False,
            )

        else:
            cleaned_df.to_excel(
                cleaned_path,
                index=False,
            )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to save cleaned dataset: {str(exc)}",
        )

    summary["cleaned_filename"] = cleaned_filename
    summary["cleaned_file_path"] = str(cleaned_path)

    return {
        "dataset_id": dataset.id,
        "original_filename": dataset.original_filename,
        "cleaned_filename": cleaned_filename,
        "download_available": True,
        "preview": summary,
    }


def get_cleaned_file_path(
    dataset: Dataset,
) -> Path:
    """
    Return the expected cleaned dataset path.
    """

    original_path = Path(dataset.file_path)

    extension = dataset.file_type.lower()

    if extension == "xls":
        extension = "xlsx"

    cleaned_path = (
        original_path.parent
        / f"{original_path.stem}_cleaned.{extension}"
    )

    if not cleaned_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Cleaned dataset has not been generated yet.",
        )

    return cleaned_path