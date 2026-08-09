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
    total_rows = len(df)

    summary = {
        "rows": total_rows,
        "columns": len(df.columns),
        "memory_usage": int(
            df.memory_usage(deep=True).sum()
        ),
        "missing_cells": int(
            df.isna().sum().sum()
        ),
        "duplicate_rows": int(
            df.duplicated().sum()
        ),
    }

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
                    df[column].nunique(dropna=True)
                ),
                "memory_usage": int(
                    df[column].memory_usage(deep=True)
                ),
            }
        )

    statistics = (
        df.describe(include="all")
        .replace({np.nan: None})
        .to_dict()
    )

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

    duplicates = {
        "count": int(
            df.duplicated().sum()
        )
    }

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

    outliers = {}

    for column in numeric_df.columns:
        q1 = numeric_df[column].quantile(0.25)
        q3 = numeric_df[column].quantile(0.75)

        iqr = q3 - q1

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outliers[str(column)] = int(
            (
                (numeric_df[column] < lower)
                | (numeric_df[column] > upper)
            ).sum()
        )

    return to_json_safe(
        {
            "summary": summary,
            "column_info": column_info,
            "statistics": statistics,
            "missing_values": missing_values,
            "duplicates": duplicates,
            "correlations": correlations,
            "outliers": outliers,
        }
    )

