import pandas as pd


def profile_dataframe(df: pd.DataFrame):

    summary = {
        "rows": len(df),
        "columns": len(df.columns),
        "memory_usage": int(
            df.memory_usage(deep=True).sum()
        ),
    }

    column_info = []

    for column in df.columns:

        column_info.append(
            {
                "name": column,
                "dtype": str(df[column].dtype),
                "missing": int(
                    df[column].isna().sum()
                ),
                "unique": int(
                    df[column].nunique()
                ),
            }
        )

    statistics = (
        df.describe(
            include="all"
        )
        .fillna("")
        .to_dict()
    )

    missing_values = (
        df.isna()
        .sum()
        .to_dict()
    )

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