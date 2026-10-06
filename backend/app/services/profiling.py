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
    """Build the canonical deterministic profile used by the application."""

    total_rows = len(df)
    total_columns = len(df.columns)
    missing_total = int(df.isna().sum().sum())

    identifier_columns = [
        column
        for column in df.columns
        if (
            str(column).strip().lower() == "id"
            or str(column).strip().lower().endswith("_id")
            or str(column).strip().lower().endswith("id")
        )
    ]
    duplicate_columns = [
        column for column in df.columns if column not in identifier_columns
    ]
    duplicate_count = int(
        df.duplicated(
            subset=duplicate_columns or None,
            keep="first",
        ).sum()
    )

    column_info: list[dict[str, Any]] = []
    statistics: dict[str, dict[str, Any]] = {}
    missing_values: dict[str, dict[str, Any]] = {}

    for column in df.columns:
        series = df[column]
        name = str(column)
        non_missing = series.dropna()
        missing_count = int(series.isna().sum())
        dtype = series.dtype

        if pd.api.types.is_bool_dtype(dtype):
            display_dtype = "boolean"
        elif pd.api.types.is_integer_dtype(dtype):
            display_dtype = "integer"
        elif pd.api.types.is_float_dtype(dtype):
            display_dtype = "float"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            display_dtype = "datetime"
        elif isinstance(dtype, pd.CategoricalDtype):
            display_dtype = "categorical"
        elif (
            pd.api.types.is_object_dtype(dtype)
            or pd.api.types.is_string_dtype(dtype)
        ):
            display_dtype = "string"
        else:
            display_dtype = str(dtype)

        column_info.append(
            {
                "name": name,
                "dtype": display_dtype,
                "pandas_dtype": str(dtype),
                "missing": missing_count,
                "missing_percent": round(
                    missing_count / total_rows * 100,
                    2,
                )
                if total_rows
                else 0.0,
                "unique": int(series.nunique(dropna=True)),
                "memory_usage": int(series.memory_usage(deep=True)),
            }
        )
        missing_values[name] = {
            "count": missing_count,
            "percent": round(
                missing_count / total_rows * 100,
                2,
            )
            if total_rows
            else 0.0,
        }

        values: dict[str, Any] = {
            "count": int(non_missing.count()),
            "unique": int(non_missing.nunique()),
        }
        if pd.api.types.is_numeric_dtype(dtype) and not pd.api.types.is_bool_dtype(dtype):
            numeric = pd.to_numeric(non_missing, errors="coerce").dropna()
            if not numeric.empty:
                mode = numeric.mode()
                q1 = numeric.quantile(0.25)
                median = numeric.median()
                q3 = numeric.quantile(0.75)
                values.update(
                    {
                        "mean": numeric.mean(),
                        "median": median,
                        "mode": mode.iloc[0] if not mode.empty else None,
                        "std": numeric.std() if len(numeric) > 1 else None,
                        "min": numeric.min(),
                        "max": numeric.max(),
                        "range": numeric.max() - numeric.min(),
                        "variance": numeric.var() if len(numeric) > 1 else None,
                        "q1": q1,
                        "q3": q3,
                        "iqr": q3 - q1,
                        "skewness": numeric.skew() if len(numeric) > 2 else None,
                        "kurtosis": numeric.kurt() if len(numeric) > 3 else None,
                        "percentile_5": numeric.quantile(0.05),
                        "percentile_95": numeric.quantile(0.95),
                    }
                )
        elif not non_missing.empty:
            mode = non_missing.mode(dropna=True)
            values.update(
                {
                    "mode": mode.iloc[0] if not mode.empty else None,
                    "top": mode.iloc[0] if not mode.empty else None,
                    "freq": int((non_missing == mode.iloc[0]).sum())
                    if not mode.empty
                    else 0,
                }
            )
        else:
            values.update({"mode": None, "top": None, "freq": 0})

        statistics[name] = values

    numeric_df = df.select_dtypes(include="number").dropna(axis=1, how="all")
    eligible_columns = [
        column
        for column in numeric_df.columns
        if numeric_df[column].dropna().nunique() > 1
        and numeric_df[column].count() >= 3
    ]
    correlations: dict[str, dict[str, float]] = {}
    if len(eligible_columns) >= 2:
        correlation_frame = numeric_df[eligible_columns].corr(
            method="pearson",
            min_periods=3,
        )
        valid_pairs: list[tuple[Any, Any, float]] = []
        for index, column_a in enumerate(eligible_columns):
            for column_b in eligible_columns[index + 1 :]:
                coefficient = correlation_frame.loc[column_a, column_b]
                if pd.notna(coefficient) and np.isfinite(coefficient):
                    valid_pairs.append((column_a, column_b, round(float(coefficient), 3)))
        related_columns = {
            column
            for column_a, column_b, _ in valid_pairs
            for column in (column_a, column_b)
        }
        correlations = {str(column): {} for column in eligible_columns if column in related_columns}
        for column in related_columns:
            correlations[str(column)][str(column)] = 1.0
        for column_a, column_b, coefficient in valid_pairs:
            correlations[str(column_a)][str(column_b)] = coefficient
            correlations[str(column_b)][str(column_a)] = coefficient

    outliers: dict[str, dict[str, Any]] = {}
    for column in numeric_df.columns:
        series = pd.to_numeric(numeric_df[column], errors="coerce").dropna()
        lower = upper = None
        count = 0
        if len(series) >= 4:
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            count = int(((series < lower) | (series > upper)).sum())
        outliers[str(column)] = {
            "count": count,
            "percentage": round(count / len(series) * 100, 2) if len(series) else 0.0,
            "method": "IQR",
            "lower_bound": lower,
            "upper_bound": upper,
        }

    duplicates = {
        "count": duplicate_count,
        "percentage": round(duplicate_count / total_rows * 100, 2)
        if total_rows
        else 0.0,
        "has_duplicates": duplicate_count > 0,
    }
    summary = {
        "rows": total_rows,
        "columns": total_columns,
        "memory_usage": int(df.memory_usage(deep=True).sum()),
        "missing_cells": missing_total,
        "duplicate_rows": duplicate_count,
    }

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