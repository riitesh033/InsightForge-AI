import pandas as pd


def profile_dataframe(df: pd.DataFrame):

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

        missing = int(df[column].isna().sum())

        column_info.append(
            {
                "name": column,
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
                    df[column]
                    .memory_usage(deep=True)
                ),
            }
        )

    statistics = (
        df.describe(include="all")
        .fillna("")
        .to_dict()
    )

    missing_values = {}

    for column in df.columns:
        count = int(df[column].isna().sum())

        missing_values[column] = {
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

    return {
        "summary": summary,
        "column_info": column_info,
        "statistics": statistics,
        "missing_values": missing_values,
        "duplicates": duplicates,
        "correlations": {},
        "outliers": {},
    }