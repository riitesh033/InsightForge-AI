from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd


def to_json_safe(obj: Any) -> Any:
    """Recursively convert pandas/numpy/Python objects into JSON-safe values."""

    # Dictionaries
    if isinstance(obj, dict):
        return {
            str(to_json_safe(key)): to_json_safe(value)
            for key, value in obj.items()
        }

    # Lists
    if isinstance(obj, list):
        return [to_json_safe(value) for value in obj]

    # Tuples
    if isinstance(obj, tuple):
        return [to_json_safe(value) for value in obj]

    # Sets
    if isinstance(obj, set):
        return [to_json_safe(value) for value in obj]

    # Pandas missing value
    if obj is pd.NA:
        return None

    # Pandas Timestamp
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()

    # Pandas Timedelta
    if isinstance(obj, pd.Timedelta):
        return str(obj)

    # NumPy datetime
    if isinstance(obj, np.datetime64):
        return pd.Timestamp(obj).isoformat()

    # Python datetime/date
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    # NumPy integer
    if isinstance(obj, np.integer):
        return int(obj)

    # NumPy floating point
    if isinstance(obj, np.floating):
        value = float(obj)

        if not np.isfinite(value):
            return None

        return value

    # NumPy boolean
    if isinstance(obj, np.bool_):
        return bool(obj)

    # NumPy array
    if isinstance(obj, np.ndarray):
        return [
            to_json_safe(value)
            for value in obj.tolist()
        ]

    # Python float
    if isinstance(obj, float):
        if not np.isfinite(obj):
            return None

        return obj

    # Handle NaN / NaT
    try:
        missing = pd.isna(obj)

        if isinstance(missing, (bool, np.bool_)) and missing:
            return None

    except (TypeError, ValueError):
        pass

    return obj


def profile_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """Generate dataset profiling information."""

    print("\n================================")
    print("PROFILE DATAFRAME CALLED")
    print("================================")

    print("DataFrame shape:", df.shape)
    print("Columns:", list(df.columns))

    total_rows = len(df)

    # ============================================================
    # DUPLICATE CHECK
    # ============================================================

    # Detect columns that look like identifiers.
    #
    # Examples:
    # id
    # employee_id
    # user_id
    # customer_id
    # product_id
    #
    # These columns are ignored when checking for duplicate
    # records because IDs are normally unique even when the
    # actual record is duplicated.

    identifier_columns = []

    for column in df.columns:

        column_name = str(column).strip().lower()

        if (
            column_name == "id"
            or column_name.endswith("_id")
            or column_name.endswith("id")
        ):
            identifier_columns.append(column)

    # Columns used to determine whether two records are duplicates.
    duplicate_columns = [
        column
        for column in df.columns
        if column not in identifier_columns
    ]

    # If there are columns remaining after removing identifier
    # columns, use them for duplicate detection.
    #
    # keep="first" means:
    # - first occurrence is considered the original
    # - subsequent occurrences are counted as duplicates
    #
    # For example:
    #
    # Rohan row 1  -> original
    # Rohan row 21 -> duplicate
    #
    # Priya row 2  -> original
    # Priya row 22 -> duplicate
    #
    # Therefore duplicate_count = 2.

    if duplicate_columns:

        duplicate_mask = df.duplicated(
            subset=duplicate_columns,
            keep=False,
        )

        duplicate_count = int(
            df.duplicated(
                subset=duplicate_columns,
                keep="first",
            ).sum()
        )

    else:

        # Fallback for datasets where every column looks like an ID.
        duplicate_mask = df.duplicated(
            keep=False,
        )

        duplicate_count = int(
            df.duplicated(
                keep="first",
            ).sum()
        )

    has_duplicates = duplicate_count > 0

    print("\n================================")
    print("DUPLICATE CHECK")
    print("================================")

    print(
        "Identifier columns ignored:",
        [str(column) for column in identifier_columns],
    )

    print(
        "Columns used for duplicate detection:",
        [str(column) for column in duplicate_columns],
    )

    print(
        "Total duplicate rows:",
        duplicate_count,
    )

    print(
        "Has duplicates:",
        has_duplicates,
    )

    print("\nDuplicate mask:")
    print(duplicate_mask)

    print("\nDuplicate rows:")
    print(df[duplicate_mask])

    print("================================\n")

    # ============================================================
    # SUMMARY
    # ============================================================

    summary = {
        "rows": total_rows,
        "columns": len(df.columns),
        "memory_usage": int(
            df.memory_usage(deep=True).sum()
        ),
        "missing_cells": int(
            df.isna().sum().sum()
        ),
        "duplicate_rows": duplicate_count,
    }

    # ============================================================
    # COLUMN INFORMATION
    # ============================================================

    column_info = []

    for column in df.columns:

        missing = int(
            df[column].isna().sum()
        )

        column_info.append(
            {
                "name": str(column),
                "dtype": str(df[column].dtype),
                "missing": missing,
                "missing_percent": round(
                    (missing / total_rows) * 100,
                    2,
                )
                if total_rows
                else 0,
                "unique": int(
                    df[column].nunique(
                        dropna=True
                    )
                ),
                "memory_usage": int(
                    df[column].memory_usage(
                        deep=True
                    )
                ),
            }
        )

    # ============================================================
    # STATISTICS
    # ============================================================

    statistics = (
        df.describe(include="all")
        .replace({np.nan: None})
        .to_dict()
    )

    # ============================================================
    # MISSING VALUES
    # ============================================================

    missing_values = {}

    for column in df.columns:

        count = int(
            df[column].isna().sum()
        )

        missing_values[str(column)] = {
            "count": count,
            "percent": round(
                (count / total_rows) * 100,
                2,
            )
            if total_rows
            else 0,
        }

    # ============================================================
    # DUPLICATES
    # ============================================================

    duplicates = {
        "count": duplicate_count,
        "has_duplicates": has_duplicates,
    }

    # ============================================================
    # CORRELATIONS
    # ============================================================

    numeric_df = df.select_dtypes(
        include="number"
    )

    if len(numeric_df.columns) >= 2:

        correlations = (
            numeric_df.corr(
                numeric_only=True
            )
            .round(3)
            .fillna(0)
            .to_dict()
        )

    else:
        correlations = {}

    # ============================================================
    # OUTLIERS
    # ============================================================

    outliers = {}

    for column in numeric_df.columns:

        series = numeric_df[column].dropna()

        if series.empty:
            outliers[str(column)] = 0
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outliers[str(column)] = int(
            (
                (series < lower)
                | (series > upper)
            ).sum()
        )

    # ============================================================
    # FINAL RESULT
    # ============================================================

    result = {
        "summary": summary,
        "column_info": column_info,
        "statistics": statistics,
        "missing_values": missing_values,
        "duplicates": duplicates,
        "correlations": correlations,
        "outliers": outliers,
    }

    print("FINAL DUPLICATE RESULT:")
    print(result["duplicates"])
    print("================================\n")

    return to_json_safe(result)