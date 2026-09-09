"""
Professional Data Analysis Service

Generates business-quality analysis reports with:
- Executive summary
- Data quality assessment
- Descriptive statistics
- Distribution analysis
- Correlation analysis
- Outlier detection
- Key insights
- Actionable recommendations
- Business opportunity analysis
"""

from typing import Any
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import stats


# ============================================================
# JSON SAFETY
# ============================================================

def to_json_safe(obj: Any) -> Any:
    """
    Recursively convert pandas/numpy/Python objects
    into JSON-safe values.
    """

    if isinstance(obj, dict):
        return {
            str(to_json_safe(key)): to_json_safe(value)
            for key, value in obj.items()
        }

    if isinstance(obj, (list, tuple, set)):
        return [to_json_safe(value) for value in obj]

    if obj is pd.NA:
        return None

    if isinstance(obj, pd.Timestamp):
        try:
            return obj.isoformat()
        except Exception:
            return str(obj)

    if isinstance(obj, pd.Timedelta):
        return str(obj)

    if isinstance(obj, np.datetime64):
        try:
            return pd.Timestamp(obj).isoformat()
        except Exception:
            return str(obj)

    if isinstance(obj, datetime):
        return obj.isoformat()

    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        value = float(obj)
        return value if np.isfinite(value) else None

    if isinstance(obj, np.bool_):
        return bool(obj)

    if isinstance(obj, np.ndarray):
        return [to_json_safe(value) for value in obj.tolist()]

    if isinstance(obj, float):
        return obj if np.isfinite(obj) else None

    if isinstance(obj, int):
        return obj

    if isinstance(obj, bool):
        return obj

    try:
        missing = pd.isna(obj)

        if isinstance(missing, (bool, np.bool_)) and missing:
            return None

    except (TypeError, ValueError):
        pass

    return obj


# ============================================================
# COLUMN TYPE DETECTION
# ============================================================

def detect_column_types(df: pd.DataFrame) -> dict[str, list[str]]:
    """
    Detect column types beyond pandas dtypes.

    Categories:
    - numerical
    - categorical
    - datetime
    - boolean
    - identifier
    """

    numerical = []
    categorical = []
    datetime_cols = []
    boolean_cols = []
    identifier = []

    for col in df.columns:

        col_str = str(col)
        col_lower = col_str.lower().strip()
        series = df[col]

        # ----------------------------------------------------
        # Datetime
        # ----------------------------------------------------

        if pd.api.types.is_datetime64_any_dtype(series):
            datetime_cols.append(col_str)
            continue

        # ----------------------------------------------------
        # Boolean
        # ----------------------------------------------------

        if pd.api.types.is_bool_dtype(series):
            boolean_cols.append(col_str)
            continue

        # ----------------------------------------------------
        # Identifier detection
        # ----------------------------------------------------

        is_identifier_name = (
            col_lower == "id"
            or col_lower.endswith("_id")
            or (
                col_lower.endswith("id")
                and col_lower not in {"paid", "valid"}
            )
        )

        if is_identifier_name:

            non_null = series.dropna()

            if (
                len(non_null) > 0
                and series.nunique(dropna=True) == len(non_null)
            ):
                identifier.append(col_str)
                continue

        # ----------------------------------------------------
        # Numerical
        # ----------------------------------------------------

        if pd.api.types.is_numeric_dtype(series):
            numerical.append(col_str)
            continue

        # ----------------------------------------------------
        # Categorical
        # ----------------------------------------------------

        unique_count = series.nunique(dropna=True)

        unique_ratio = (
            unique_count / len(series)
            if len(series) > 0
            else 0
        )

        if (
            pd.api.types.is_object_dtype(series)
            or pd.api.types.is_string_dtype(series)
            or (
                unique_ratio < 0.1
                and unique_count < 50
            )
        ):
            categorical.append(col_str)
            continue

        # Default
        categorical.append(col_str)

    return {
        "numerical": numerical,
        "categorical": categorical,
        "datetime": datetime_cols,
        "boolean": boolean_cols,
        "identifier": identifier,
    }


# ============================================================
# DESCRIPTIVE STATISTICS
# ============================================================

def calculate_descriptive_statistics(
    df: pd.DataFrame,
    column_types: dict
) -> dict:
    """
    Calculate comprehensive descriptive statistics.
    """

    statistics = {}

    # --------------------------------------------------------
    # Numerical columns
    # --------------------------------------------------------

    for col in column_types.get("numerical", []):

        if col not in df.columns:
            continue

        series = pd.to_numeric(
            df[col],
            errors="coerce"
        ).dropna()

        if len(series) == 0:
            continue

        mode_values = series.mode()

        stats_dict = {
            "count": int(len(series)),
            "mean": float(series.mean()),
            "median": float(series.median()),
            "mode": (
                float(mode_values.iloc[0])
                if len(mode_values) > 0
                else None
            ),
            "min": float(series.min()),
            "max": float(series.max()),
            "range": float(series.max() - series.min()),
            "std": (
                float(series.std())
                if len(series) > 1
                else None
            ),
            "variance": (
                float(series.var())
                if len(series) > 1
                else None
            ),
            "q1": float(series.quantile(0.25)),
            "q3": float(series.quantile(0.75)),
            "iqr": float(
                series.quantile(0.75)
                - series.quantile(0.25)
            ),
            "skewness": (
                float(stats.skew(series))
                if len(series) > 2
                else None
            ),
            "kurtosis": (
                float(stats.kurtosis(series))
                if len(series) > 3
                else None
            ),
            "percentile_5": float(
                series.quantile(0.05)
            ),
            "percentile_95": float(
                series.quantile(0.95)
            ),
            "coefficient_of_variation": (
                float(series.std() / series.mean())
                if (
                    len(series) > 1
                    and series.mean() != 0
                )
                else None
            ),
        }

        statistics[col] = to_json_safe(stats_dict)

    # --------------------------------------------------------
    # Categorical columns
    # --------------------------------------------------------

    for col in column_types.get("categorical", []):

        if col not in df.columns:
            continue

        series = df[col].dropna()

        if len(series) == 0:
            continue

        value_counts = series.value_counts()

        if len(value_counts) == 0:
            continue

        top_value = value_counts.index[0]
        top_count = int(value_counts.iloc[0])

        distribution = {}

        for value, count in value_counts.head(5).items():

            distribution[str(value)] = {
                "count": int(count),
                "percentage": round(
                    (count / len(series)) * 100,
                    2
                ),
            }

        stats_dict = {
            "count": int(len(series)),
            "unique": int(series.nunique()),
            "top_value": str(top_value),
            "top_frequency": top_count,
            "top_percentage": round(
                (top_count / len(series)) * 100,
                2
            ),
            "distribution": distribution,
        }

        statistics[col] = stats_dict

    # --------------------------------------------------------
    # Datetime columns
    # --------------------------------------------------------

    for col in column_types.get("datetime", []):

        if col not in df.columns:
            continue

        series = pd.to_datetime(
            df[col],
            errors="coerce"
        ).dropna()

        if len(series) == 0:
            continue

        min_date = series.min()
        max_date = series.max()

        stats_dict = {
            "count": int(len(series)),
            "min_date": min_date.isoformat(),
            "max_date": max_date.isoformat(),
            "time_span_days": (
                int((max_date - min_date).days)
                if len(series) > 1
                else 0
            ),
        }

        statistics[col] = stats_dict

    return to_json_safe(statistics)


# ============================================================
# DATA QUALITY
# ============================================================

def analyze_data_quality(
    df: pd.DataFrame,
    column_types: dict
) -> dict:
    """
    Comprehensive data quality assessment.
    """

    total_rows = len(df)

    if total_rows == 0:
        return {
            "quality_score": 0,
            "total_issues": 1,
            "issues": [
                {
                    "type": "empty_dataset",
                    "column": "all",
                    "count": 0,
                    "percentage": 100.0,
                    "severity": "high",
                    "recommendation": (
                        "Upload a dataset containing at least one record."
                    ),
                }
            ],
            "summary": {
                "excellent": False,
                "good": False,
                "fair": False,
                "poor": True,
            },
        }

    issues = []

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    for col in df.columns:

        missing_count = int(df[col].isna().sum())

        if missing_count == 0:
            continue

        missing_percent = round(
            (missing_count / total_rows) * 100,
            2
        )

        severity = "low"

        if missing_percent > 30:
            severity = "high"
        elif missing_percent > 10:
            severity = "medium"

        col_type = "unknown"

        for type_name, cols in column_types.items():
            if col in cols:
                col_type = type_name
                break

        if col_type == "numerical":
            recommendation = (
                "Consider median-based imputation after "
                "checking the missingness pattern."
            )
        elif col_type == "categorical":
            recommendation = (
                "Consider using the most frequent value "
                "or an explicit Unknown category."
            )
        else:
            recommendation = (
                "Investigate the source of the missing values "
                "before deciding on an imputation strategy."
            )

        if missing_percent > 50:
            recommendation = (
                "Consider removing this column or investigating "
                "the source of excessive missing values."
            )

        issues.append({
            "type": "missing_values",
            "column": str(col),
            "count": missing_count,
            "percentage": missing_percent,
            "severity": severity,
            "recommendation": recommendation,
        })

    # --------------------------------------------------------
    # Duplicate rows
    # --------------------------------------------------------

    duplicate_count = int(df.duplicated().sum())

    if duplicate_count > 0:

        duplicate_percent = round(
            (duplicate_count / total_rows) * 100,
            2
        )

        severity = "low"

        if duplicate_percent > 20:
            severity = "high"
        elif duplicate_percent > 5:
            severity = "medium"

        issues.append({
            "type": "duplicates",
            "column": "all",
            "count": duplicate_count,
            "percentage": duplicate_percent,
            "severity": severity,
            "recommendation": (
                "Investigate whether duplicate records are valid "
                "or accidental. Remove exact duplicates when appropriate."
            ),
        })

    # --------------------------------------------------------
    # Constant columns
    # --------------------------------------------------------

    for col in df.columns:

        if (
            df[col].nunique(dropna=True) == 1
            and df[col].notna().any()
        ):
            issues.append({
                "type": "constant_column",
                "column": str(col),
                "count": 1,
                "percentage": 100.0,
                "severity": "low",
                "recommendation": (
                    "This column has no variance and may not "
                    "provide analytical value."
                ),
            })

    # --------------------------------------------------------
    # High cardinality
    # --------------------------------------------------------

    for col in column_types.get("categorical", []):

        if col not in df.columns:
            continue

        unique_count = df[col].nunique(dropna=True)

        unique_ratio = (
            unique_count / total_rows
            if total_rows > 0
            else 0
        )

        if unique_count > 100 and unique_ratio > 0.5:

            issues.append({
                "type": "high_cardinality",
                "column": str(col),
                "count": int(unique_count),
                "percentage": round(
                    unique_ratio * 100,
                    2
                ),
                "severity": "medium",
                "recommendation": (
                    "Consider grouping rare categories "
                    "if detailed categories are not required."
                ),
            })

    # --------------------------------------------------------
    # Outliers
    # --------------------------------------------------------

    for col in column_types.get("numerical", []):

        if col not in df.columns:
            continue

        series = pd.to_numeric(
            df[col],
            errors="coerce"
        ).dropna()

        if len(series) < 4:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        if iqr == 0:
            continue

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        outliers = (
            (series < lower_bound)
            | (series > upper_bound)
        ).sum()

        if outliers > 0:

            outlier_percent = round(
                (outliers / len(series)) * 100,
                2
            )

            severity = "low"

            if outlier_percent > 10:
                severity = "high"
            elif outlier_percent > 5:
                severity = "medium"

            issues.append({
                "type": "outliers",
                "column": str(col),
                "count": int(outliers),
                "percentage": outlier_percent,
                "severity": severity,
                "recommendation": (
                    "Investigate whether outliers are data-entry "
                    "errors or legitimate extreme observations."
                ),
            })

    # --------------------------------------------------------
    # Quality score
    # --------------------------------------------------------

    score = 100

    for issue in issues:

        if issue["severity"] == "high":
            score -= 15

        elif issue["severity"] == "medium":
            score -= 8

        else:
            score -= 3

    score = max(0, min(100, score))

    return {
        "quality_score": score,
        "total_issues": len(issues),
        "issues": issues,
        "summary": {
            "excellent": score >= 90,
            "good": 75 <= score < 90,
            "fair": 50 <= score < 75,
            "poor": score < 50,
        },
    }


# ============================================================
# DISTRIBUTION ANALYSIS
# ============================================================

def analyze_distributions(
    df: pd.DataFrame,
    column_types: dict
) -> dict:
    """
    Analyze distribution characteristics
    for numerical columns.
    """

    distributions = {}

    for col in column_types.get("numerical", []):

        if col not in df.columns:
            continue

        series = pd.to_numeric(
            df[col],
            errors="coerce"
        ).dropna()

        if len(series) < 4:
            continue

        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------

        mean = float(series.mean())
        median = float(series.median())

        std = float(series.std())

        # IMPORTANT:
        # scipy.stats has skew(), NOT skewness()
        skewness = float(stats.skew(series))

        kurtosis = float(stats.kurtosis(series))

        # ----------------------------------------------------
        # Distribution shape
        # ----------------------------------------------------

        shape = "unknown"

        if np.isfinite(skewness):

            if abs(skewness) < 0.5:
                shape = "approximately_symmetric"

            elif skewness > 0:
                shape = "right_skewed"

            else:
                shape = "left_skewed"

        # ----------------------------------------------------
        # Variance level
        # ----------------------------------------------------

        if mean != 0:
            cv = std / abs(mean)
        else:
            cv = 0.0

        if abs(cv) > 1:
            variance_level = "high"

        elif abs(cv) < 0.3:
            variance_level = "low"

        else:
            variance_level = "moderate"

        # ----------------------------------------------------
        # Concentration
        # ----------------------------------------------------

        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))

        iqr = q3 - q1

        range_val = float(
            series.max() - series.min()
        )

        concentration = "normal"

        if range_val > 0:

            ratio = iqr / range_val

            if ratio < 0.2:
                concentration = "highly_concentrated"

            elif ratio > 0.6:
                concentration = "widely_spread"

        # ----------------------------------------------------
        # Outliers
        # ----------------------------------------------------

        if iqr > 0:

            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)

            has_outliers = bool(
                (
                    (series < lower_bound)
                    | (series > upper_bound)
                ).any()
            )

        else:
            has_outliers = False

        distributions[col] = {
            "shape": shape,
            "skewness": round(skewness, 3),
            "kurtosis": round(kurtosis, 3),
            "variance_level": variance_level,
            "coefficient_of_variation": round(cv, 3),
            "concentration": concentration,
            "has_outliers": has_outliers,
            "mean": round(mean, 4),
            "median": round(median, 4),
        }

    return to_json_safe(distributions)


# ============================================================
# CORRELATION ANALYSIS
# ============================================================

def analyze_correlations(
    df: pd.DataFrame,
    column_types: dict
) -> dict:
    """
    Analyze correlations between numerical variables.
    """

    numerical_columns = [
        col
        for col in column_types.get("numerical", [])
        if col in df.columns
    ]

    if len(numerical_columns) < 2:
        return {
            "matrix": {},
            "pairs": [],
            "interpretation": [],
        }

    numerical_df = df[numerical_columns].apply(
        pd.to_numeric,
        errors="coerce"
    )

    if len(numerical_df) < 3:
        return {
            "matrix": {},
            "pairs": [],
            "interpretation": [],
        }

    # --------------------------------------------------------
    # Correlation matrix
    # --------------------------------------------------------

    corr_matrix = numerical_df.corr(
        method="pearson"
    ).round(3)

    pairs = []
    interpretation = []

    columns = list(corr_matrix.columns)

    # --------------------------------------------------------
    # Extract pairs
    # --------------------------------------------------------

    for i in range(len(columns)):

        for j in range(i + 1, len(columns)):

            col1 = columns[i]
            col2 = columns[j]

            corr_value = corr_matrix.loc[
                col1,
                col2
            ]

            if pd.isna(corr_value):
                continue

            corr_value = float(corr_value)

            abs_corr = abs(corr_value)

            if abs_corr >= 0.7:
                strength = "strong"

            elif abs_corr >= 0.4:
                strength = "moderate"

            else:
                strength = "weak"

            direction = (
                "positive"
                if corr_value >= 0
                else "negative"
            )

            pairs.append({
                "first": str(col1),
                "second": str(col2),
                "value": round(corr_value, 3),
                "strength": strength,
                "direction": direction,
            })

            # Only meaningful correlations
            if abs_corr >= 0.6:

                interpretation.append({
                    "columns": [
                        str(col1),
                        str(col2)
                    ],
                    "correlation": round(
                        corr_value,
                        3
                    ),
                    "interpretation": (
                        f"{col1} and {col2} show a "
                        f"{strength} {direction} correlation "
                        f"(r = {corr_value:.3f}). "
                        f"This indicates that the variables "
                        f"tend to move together, but correlation "
                        f"does not imply causation."
                    ),
                })

    pairs.sort(
        key=lambda x: abs(x["value"]),
        reverse=True
    )

    return to_json_safe({
        "matrix": corr_matrix.to_dict(),
        "pairs": pairs,
        "interpretation": interpretation,
    })


# ============================================================
# KEY INSIGHTS
# ============================================================

def generate_key_insights(
    df: pd.DataFrame,
    column_types: dict,
    statistics: dict,
    quality: dict,
    correlations: dict,
    distributions: dict,
) -> list[dict]:
    """
    Generate meaningful insights from analysis.
    """

    insights = []

    total_rows = len(df)

    # --------------------------------------------------------
    # Insight 1: Data quality
    # --------------------------------------------------------

    if quality["total_issues"] > 0:

        high_severity_issues = [
            issue
            for issue in quality["issues"]
            if issue["severity"] == "high"
        ]

        if high_severity_issues:

            issue_types = sorted(
                set(
                    issue["type"]
                    for issue in high_severity_issues
                )
            )

            insights.append({
                "category": "data_quality",
                "finding": (
                    f"Critical data quality issues detected "
                    f"in {len(high_severity_issues)} area(s)."
                ),
                "evidence": (
                    f"Quality score: "
                    f"{quality['quality_score']}/100. "
                    f"Issues include: "
                    f"{', '.join(issue_types)}."
                ),
                "impact": (
                    "Poor data quality can lead to inaccurate "
                    "analysis and misleading conclusions."
                ),
                "recommendation": (
                    "Address high-severity issues before "
                    "making important decisions."
                ),
            })

    # --------------------------------------------------------
    # Insight 2: Missing values
    # --------------------------------------------------------

    missing_issues = [
        issue
        for issue in quality["issues"]
        if (
            issue["type"] == "missing_values"
            and issue["percentage"] > 5
        )
    ]

    if missing_issues:

        worst_missing = max(
            missing_issues,
            key=lambda x: x["percentage"]
        )

        insights.append({
            "category": "data_quality",
            "finding": (
                f"Column '{worst_missing['column']}' "
                f"has significant missing values "
                f"({worst_missing['percentage']}%)."
            ),
            "evidence": (
                f"{worst_missing['count']} out of "
                f"{total_rows} records are missing "
                f"in this column."
            ),
            "impact": (
                "Missing data can bias analysis results "
                "and reduce statistical reliability."
            ),
            "recommendation": (
                f"Investigate why data is missing in "
                f"'{worst_missing['column']}' and choose "
                f"an appropriate treatment."
            ),
        })

    # --------------------------------------------------------
    # Insight 3: Correlations
    # --------------------------------------------------------

    strong_correlations = [
        pair
        for pair in correlations.get("pairs", [])
        if abs(pair["value"]) >= 0.7
    ]

    if strong_correlations:

        strongest = strong_correlations[0]

        insights.append({
            "category": "relationships",
            "finding": (
                f"Strong relationship detected between "
                f"'{strongest['first']}' and "
                f"'{strongest['second']}'."
            ),
            "evidence": (
                f"Correlation coefficient: "
                f"{strongest['value']:.3f}"
            ),
            "impact": (
                "The variables move together strongly, "
                "which may indicate redundancy or an "
                "important business relationship."
            ),
            "recommendation": (
                "Investigate the relationship further "
                "and consider whether another variable "
                "could explain the observed association."
            ),
        })

    # --------------------------------------------------------
    # Insight 4: Outliers
    # --------------------------------------------------------

    outlier_issues = [
        issue
        for issue in quality["issues"]
        if (
            issue["type"] == "outliers"
            and issue["percentage"] > 5
        )
    ]

    if outlier_issues:

        worst_outlier = max(
            outlier_issues,
            key=lambda x: x["percentage"]
        )

        insights.append({
            "category": "anomalies",
            "finding": (
                f"Significant outliers detected in "
                f"'{worst_outlier['column']}'."
            ),
            "evidence": (
                f"{worst_outlier['count']} values "
                f"({worst_outlier['percentage']}%) "
                f"fall outside the IQR-based range."
            ),
            "impact": (
                "Outliers can disproportionately influence "
                "statistical measures and machine-learning models."
            ),
            "recommendation": (
                "Verify whether these observations are "
                "legitimate extreme values or data errors."
            ),
        })

    # --------------------------------------------------------
    # Insight 5: Distribution
    # --------------------------------------------------------

    skewed_cols = [
        (col, distribution)
        for col, distribution in distributions.items()
        if distribution.get("shape") in [
            "right_skewed",
            "left_skewed"
        ]
    ]

    if skewed_cols:

        most_skewed = max(
            skewed_cols,
            key=lambda x: abs(
                x[1].get("skewness", 0)
            )
        )

        insights.append({
            "category": "distribution",
            "finding": (
                f"Column '{most_skewed[0]}' shows "
                f"{most_skewed[1]['shape'].replace('_', ' ')}."
            ),
            "evidence": (
                f"Skewness coefficient: "
                f"{most_skewed[1].get('skewness', 0):.3f}"
            ),
            "impact": (
                "Skewed distributions may affect statistical "
                "methods that assume approximately normal data."
            ),
            "recommendation": (
                "Consider a transformation such as logarithmic "
                "or square-root transformation when appropriate."
            ),
        })

    # --------------------------------------------------------
    # Insight 6: Business analysis
    # --------------------------------------------------------

    revenue_col = None
    cost_col = None

    for col in df.columns:

        col_lower = str(col).lower()

        if revenue_col is None and any(
            term in col_lower
            for term in [
                "revenue",
                "sales",
                "amount",
                "price"
            ]
        ):
            revenue_col = col

        if cost_col is None and any(
            term in col_lower
            for term in [
                "cost",
                "expense"
            ]
        ):
            cost_col = col

    if (
        revenue_col is not None
        and revenue_col in statistics
    ):

        rev_stats = statistics[revenue_col]

        insights.append({
            "category": "business",
            "finding": (
                f"'{revenue_col}' shows measurable "
                f"variation across records."
            ),
            "evidence": (
                f"Mean: {rev_stats.get('mean', 0):,.2f}, "
                f"Std Dev: {rev_stats.get('std', 0) or 0:,.2f}, "
                f"Range: "
                f"{rev_stats.get('min', 0):,.2f} to "
                f"{rev_stats.get('max', 0):,.2f}"
            ),
            "impact": (
                "Variation may provide opportunities "
                "for segmentation and optimization."
            ),
            "recommendation": (
                "Segment revenue by available product, "
                "customer, category, or region fields."
            ),
        })

    # --------------------------------------------------------
    # Insight 7: Profit margin
    # --------------------------------------------------------

    if (
        revenue_col is not None
        and cost_col is not None
        and revenue_col in df.columns
        and cost_col in df.columns
    ):

        revenue = pd.to_numeric(
            df[revenue_col],
            errors="coerce"
        )

        cost = pd.to_numeric(
            df[cost_col],
            errors="coerce"
        )

        valid = (
            revenue.notna()
            & cost.notna()
            & (revenue != 0)
        )

        if valid.any():

            profit = revenue[valid] - cost[valid]

            margin = (
                profit / revenue[valid]
            ) * 100

            average_margin = float(
                margin.replace(
                    [np.inf, -np.inf],
                    np.nan
                ).dropna().mean()
            )

            insights.append({
                "category": "business",
                "finding": (
                    f"Average estimated profit margin "
                    f"is approximately "
                    f"{average_margin:.1f}%."
                ),
                "evidence": (
                    f"Calculated using '{revenue_col}' "
                    f"and '{cost_col}'."
                ),
                "impact": (
                    "Margin analysis can reveal profitable "
                    "and underperforming segments."
                ),
                "recommendation": (
                    "Compare margins across products, "
                    "customers, or other available segments."
                ),
            })

    # --------------------------------------------------------
    # Insight 8: Dataset size
    # --------------------------------------------------------

    if total_rows < 100:

        insights.append({
            "category": "methodology",
            "finding": "Dataset is relatively small.",
            "evidence": (
                f"Only {total_rows} records are available."
            ),
            "impact": (
                "Small samples can limit statistical power "
                "and generalizability."
            ),
            "recommendation": (
                "Collect more observations where possible "
                "and interpret statistical conclusions cautiously."
            ),
        })

    elif total_rows > 100000:

        insights.append({
            "category": "methodology",
            "finding": (
                "Large dataset provides a strong "
                "statistical foundation."
            ),
            "evidence": (
                f"{total_rows:,} records are available."
            ),
            "impact": (
                "Large datasets can support robust "
                "statistical analysis."
            ),
            "recommendation": (
                "Consider sampling for exploratory analysis "
                "when performance becomes a concern."
            ),
        })

    return to_json_safe(insights[:8])


# ============================================================
# RECOMMENDATIONS
# ============================================================

def generate_recommendations(
    df: pd.DataFrame,
    column_types: dict,
    quality: dict,
    insights: list[dict]
) -> dict:
    """
    Generate prioritized actionable recommendations.
    """

    high_priority = []
    medium_priority = []
    low_priority = []

    # --------------------------------------------------------
    # High priority
    # --------------------------------------------------------

    critical_issues = [
        issue
        for issue in quality["issues"]
        if issue["severity"] == "high"
    ]

    for issue in critical_issues:

        if issue["type"] == "missing_values":

            high_priority.append({
                "action": (
                    f"Fix missing values in "
                    f"'{issue['column']}'"
                ),
                "reason": (
                    f"{issue['percentage']}% of values are missing"
                ),
                "evidence": (
                    f"{issue['count']} records affected"
                ),
                "benefit": (
                    "Improved data completeness "
                    "and analysis reliability"
                ),
                "risk": (
                    "Imputation may introduce bias "
                    "if missingness is not random"
                ),
            })

        elif issue["type"] == "outliers":

            high_priority.append({
                "action": (
                    f"Investigate outliers in "
                    f"'{issue['column']}'"
                ),
                "reason": (
                    f"{issue['count']} extreme values detected"
                ),
                "evidence": (
                    f"{issue['percentage']}% of observations "
                    f"are classified as outliers"
                ),
                "benefit": (
                    "More reliable statistical measures"
                ),
                "risk": (
                    "Removing legitimate outliers "
                    "may discard important information"
                ),
            })

    # --------------------------------------------------------
    # Medium priority
    # --------------------------------------------------------

    medium_issues = [
        issue
        for issue in quality["issues"]
        if issue["severity"] == "medium"
    ]

    for issue in medium_issues:

        if issue["type"] == "duplicates":

            medium_priority.append({
                "action": (
                    "Review and remove duplicate records"
                ),
                "reason": (
                    f"{issue['count']} duplicate rows found"
                ),
                "evidence": (
                    f"{issue['percentage']}% of dataset "
                    f"contains duplicates"
                ),
                "benefit": (
                    "Cleaner dataset and more accurate aggregations"
                ),
                "risk": (
                    "Some duplicates may represent "
                    "legitimate repeated transactions"
                ),
            })

        elif issue["type"] == "high_cardinality":

            medium_priority.append({
                "action": (
                    f"Review high-cardinality column "
                    f"'{issue['column']}'"
                ),
                "reason": (
                    "Large number of unique values"
                ),
                "evidence": (
                    f"{issue['count']} unique values"
                ),
                "benefit": (
                    "Simpler segmentation and analysis"
                ),
                "risk": (
                    "Grouping categories may reduce granularity"
                ),
            })

    # --------------------------------------------------------
    # Constant columns
    # --------------------------------------------------------

    constant_cols = [
        issue
        for issue in quality["issues"]
        if issue["type"] == "constant_column"
    ]

    if constant_cols:

        low_priority.append({
            "action": (
                "Consider removing constant columns: "
                + ", ".join(
                    issue["column"]
                    for issue in constant_cols
                )
            ),
            "reason": "These columns have no variance",
            "evidence": (
                "Constant columns provide little analytical value"
            ),
            "benefit": (
                "Reduced memory usage and simpler analysis"
            ),
            "risk": (
                "Usually minimal, but verify business relevance first"
            ),
        })

    # --------------------------------------------------------
    # Datetime analysis
    # --------------------------------------------------------

    datetime_columns = column_types.get(
        "datetime",
        []
    )

    if datetime_columns:

        medium_priority.append({
            "action": "Perform time-series analysis",
            "reason": (
                "Temporal information is available"
            ),
            "evidence": (
                f"Date columns detected: "
                f"{', '.join(datetime_columns)}"
            ),
            "benefit": (
                "Identify trends, seasonality, "
                "and temporal patterns"
            ),
            "risk": (
                "Requires sufficient time span "
                "for meaningful conclusions"
            ),
        })

    # --------------------------------------------------------
    # Segmentation
    # --------------------------------------------------------

    categorical_columns = column_types.get(
        "categorical",
        []
    )

    if len(categorical_columns) > 2:

        medium_priority.append({
            "action": "Perform segmentation analysis",
            "reason": (
                "Multiple categorical variables are available"
            ),
            "evidence": (
                f"Categorical columns: "
                f"{', '.join(categorical_columns[:5])}"
            ),
            "benefit": (
                "Discover distinct groups "
                "and performance differences"
            ),
            "risk": (
                "Over-segmentation may reduce actionability"
            ),
        })

    # --------------------------------------------------------
    # Default high priority
    # --------------------------------------------------------

    if not high_priority:

        high_priority.append({
            "action": (
                "Proceed with standard analysis workflow"
            ),
            "reason": (
                "No critical data quality issues detected"
            ),
            "evidence": (
                f"Quality score: "
                f"{quality['quality_score']}/100"
            ),
            "benefit": (
                "Efficient progression to deeper analysis"
            ),
            "risk": (
                "Continue monitoring data quality "
                "as new data is added"
            ),
        })

    return to_json_safe({
        "high_priority": high_priority,
        "medium_priority": medium_priority,
        "low_priority": low_priority,
    })


# ============================================================
# BUSINESS OPPORTUNITIES
# ============================================================

def analyze_business_opportunities(
    df: pd.DataFrame,
    column_types: dict
) -> dict:
    """
    Analyze potential business opportunities
    if relevant columns exist.
    """

    opportunities = []

    required_columns = {
        "revenue": [
            "revenue",
            "sales",
            "amount",
            "price",
            "total"
        ],
        "cost": [
            "cost",
            "expense",
            "cogs"
        ],
        "profit": [
            "profit",
            "margin",
            "earnings"
        ],
        "product": [
            "product",
            "item",
            "sku",
            "category"
        ],
        "customer": [
            "customer",
            "client",
            "user",
            "buyer"
        ],
        "date": [
            "date",
            "time",
            "timestamp",
            "order_date"
        ],
        "quantity": [
            "quantity",
            "units",
            "qty",
            "count"
        ],
    }

    # --------------------------------------------------------
    # Map business concepts
    # --------------------------------------------------------

    column_mapping = {}

    for concept, terms in required_columns.items():

        for col in df.columns:

            col_lower = str(col).lower()

            if any(
                term in col_lower
                for term in terms
            ):

                column_mapping[concept] = col
                break

    # --------------------------------------------------------
    # Profit
    # --------------------------------------------------------

    can_calculate_profit = False

    if (
        "revenue" in column_mapping
        and "cost" in column_mapping
    ):

        revenue_col = column_mapping["revenue"]
        cost_col = column_mapping["cost"]

        revenue = pd.to_numeric(
            df[revenue_col],
            errors="coerce"
        )

        cost = pd.to_numeric(
            df[cost_col],
            errors="coerce"
        )

        valid = (
            revenue.notna()
            & cost.notna()
        )

        if valid.any():

            can_calculate_profit = True

            valid_revenue = revenue[valid]
            valid_cost = cost[valid]

            profit = (
                valid_revenue
                - valid_cost
            )

            margin = pd.Series(
                np.nan,
                index=valid_revenue.index,
                dtype=float
            )

            non_zero = valid_revenue != 0

            margin.loc[non_zero] = (
                profit[non_zero]
                / valid_revenue[non_zero]
            ) * 100

            margin = margin.replace(
                [np.inf, -np.inf],
                np.nan
            ).dropna()

            opportunities.append({
                "type": "profit_analysis",
                "finding": (
                    "Profit can be calculated "
                    "from available revenue and cost data."
                ),
                "metrics": {
                    "average_profit": (
                        float(profit.mean())
                        if len(profit) > 0
                        else None
                    ),
                    "average_margin_percent": (
                        float(margin.mean())
                        if len(margin) > 0
                        else None
                    ),
                    "total_profit": (
                        float(profit.sum())
                        if len(profit) > 0
                        else None
                    ),
                },
                "recommendation": (
                    "Analyze profit by product, "
                    "customer, or category to identify "
                    "optimization opportunities."
                ),
            })

    # --------------------------------------------------------
    # Product analysis
    # --------------------------------------------------------

    if (
        "product" in column_mapping
        and "revenue" in column_mapping
    ):

        product_col = column_mapping["product"]
        revenue_col = column_mapping["revenue"]

        revenue_values = pd.to_numeric(
            df[revenue_col],
            errors="coerce"
        )

        temp_df = pd.DataFrame({
            "product": df[product_col],
            "revenue": revenue_values,
        }).dropna(subset=["product", "revenue"])

        if len(temp_df) > 0:

            product_revenue = (
                temp_df
                .groupby("product")["revenue"]
                .agg(
                    total_revenue="sum",
                    avg_revenue="mean",
                    transaction_count="count"
                )
                .reset_index()
                .sort_values(
                    "total_revenue",
                    ascending=False
                )
            )

            if len(product_revenue) > 0:

                top_product = product_revenue.iloc[0]

                total_revenue = (
                    product_revenue["total_revenue"]
                    .sum()
                )

                top_5_revenue = (
                    product_revenue
                    .head(5)["total_revenue"]
                    .sum()
                )

                concentration = (
                    (
                        top_5_revenue
                        / total_revenue
                    ) * 100
                    if total_revenue > 0
                    else None
                )

                opportunities.append({
                    "type": "product_performance",
                    "finding": (
                        "Top product by revenue identified."
                    ),
                    "metrics": {
                        "top_product": str(
                            top_product["product"]
                        ),
                        "top_product_revenue": float(
                            top_product["total_revenue"]
                        ),
                        "top_5_revenue_concentration": (
                            float(concentration)
                            if concentration is not None
                            else None
                        ),
                    },
                    "recommendation": (
                        "Investigate what makes top-performing "
                        "products successful and whether their "
                        "strategy can be replicated."
                    ),
                })

    # --------------------------------------------------------
    # Customer analysis
    # --------------------------------------------------------

    if (
        "customer" in column_mapping
        and "revenue" in column_mapping
    ):

        customer_col = column_mapping["customer"]
        revenue_col = column_mapping["revenue"]

        revenue_values = pd.to_numeric(
            df[revenue_col],
            errors="coerce"
        )

        temp_df = pd.DataFrame({
            "customer": df[customer_col],
            "revenue": revenue_values,
        }).dropna(
            subset=["customer", "revenue"]
        )

        if len(temp_df) > 0:

            customer_revenue = (
                temp_df
                .groupby("customer")["revenue"]
                .sum()
                .reset_index()
                .sort_values(
                    "revenue",
                    ascending=False
                )
            )

            if len(customer_revenue) > 0:

                customer_count = len(
                    customer_revenue
                )

                top_count = max(
                    1,
                    int(np.ceil(
                        customer_count * 0.2
                    ))
                )

                top_customers = (
                    customer_revenue
                    .head(top_count)
                )

                total_revenue = (
                    customer_revenue["revenue"]
                    .sum()
                )

                top_revenue = (
                    top_customers["revenue"]
                    .sum()
                )

                concentration = (
                    (
                        top_revenue
                        / total_revenue
                    ) * 100
                    if total_revenue != 0
                    else 0
                )

                opportunities.append({
                    "type": "customer_concentration",
                    "finding": (
                        "Customer revenue concentration "
                        "has been analyzed."
                    ),
                    "metrics": {
                        "top_20_percent_customers_revenue_share": (
                            float(concentration)
                        ),
                        "total_customers": int(
                            customer_count
                        ),
                    },
                    "recommendation": (
                        "If revenue concentration is very high, "
                        "consider customer diversification "
                        "to reduce dependency risk."
                    ),
                })

    # --------------------------------------------------------
    # Time-based analysis
    # --------------------------------------------------------

    if (
        "date" in column_mapping
        and "revenue" in column_mapping
    ):

        date_col = column_mapping["date"]
        revenue_col = column_mapping["revenue"]

        try:

            dates = pd.to_datetime(
                df[date_col],
                errors="coerce"
            )

            revenue = pd.to_numeric(
                df[revenue_col],
                errors="coerce"
            )

            temp_df = pd.DataFrame({
                "date": dates,
                "revenue": revenue,
            }).dropna(
                subset=["date", "revenue"]
            )

            if len(temp_df) > 1:

                temp_df = temp_df.sort_values("date")

                temp_df = temp_df.set_index("date")

                # "ME" = month end.
                # Fall back to "M" for older pandas versions.
                try:
                    monthly_revenue = (
                        temp_df["revenue"]
                        .resample("ME")
                        .sum()
                    )
                except ValueError:
                    monthly_revenue = (
                        temp_df["revenue"]
                        .resample("M")
                        .sum()
                    )

                monthly_revenue = monthly_revenue.dropna()

                if len(monthly_revenue) > 1:

                    changes = monthly_revenue.diff().dropna()

                    average_change = (
                        float(changes.mean())
                        if len(changes) > 0
                        else None
                    )

                    if average_change is None:
                        trend_direction = "stable"

                    elif average_change > 0:
                        trend_direction = "increasing"

                    elif average_change < 0:
                        trend_direction = "decreasing"

                    else:
                        trend_direction = "stable"

                    opportunities.append({
                        "type": "temporal_trend",
                        "finding": (
                            "Temporal revenue trend analysis "
                            "is available."
                        ),
                        "metrics": {
                            "average_monthly_change": (
                                average_change
                            ),
                            "trend_direction": (
                                trend_direction
                            ),
                        },
                        "recommendation": (
                            "Investigate factors driving "
                            "the observed trend and check "
                            "for seasonal patterns."
                        ),
                    })

        except Exception as exc:
            print(
                f"Warning: Time-based business analysis "
                f"failed: {exc}"
            )

    # --------------------------------------------------------
    # No business opportunities
    # --------------------------------------------------------

    if not opportunities:

        missing = [
            concept
            for concept in required_columns.keys()
            if concept not in column_mapping
        ]

        opportunities.append({
            "type": "data_requirements",
            "finding": (
                "Limited business analysis is possible "
                "with the current columns."
            ),
            "missing_columns": missing,
            "recommendation": (
                "Add business-related fields such as "
                + ", ".join(missing)
                + " when available."
            ),
        })

    return to_json_safe({
        "available_metrics": list(
            column_mapping.keys()
        ),
        "can_calculate_profit": can_calculate_profit,
        "opportunities": opportunities,
    })


# ============================================================
# MAIN PROFESSIONAL ANALYSIS
# ============================================================

def generate_professional_analysis(
    df: pd.DataFrame
) -> dict:
    """
    Main function that generates the complete
    professional analysis.
    """

    print("\n========================================")
    print("GENERATING PROFESSIONAL ANALYSIS")
    print("========================================\n")

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if df is None:
        raise ValueError(
            "DataFrame cannot be None."
        )

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "Expected a pandas DataFrame."
        )

    # --------------------------------------------------------
    # Step 1
    # --------------------------------------------------------

    print(
        "Step 1: Detecting column types..."
    )

    column_types = detect_column_types(df)

    print(
        f"  Numerical: "
        f"{len(column_types['numerical'])}"
    )

    print(
        f"  Categorical: "
        f"{len(column_types['categorical'])}"
    )

    print(
        f"  Datetime: "
        f"{len(column_types['datetime'])}"
    )

    print(
        f"  Boolean: "
        f"{len(column_types['boolean'])}"
    )

    print(
        f"  Identifier: "
        f"{len(column_types['identifier'])}"
    )

    print()

    # --------------------------------------------------------
    # Step 2
    # --------------------------------------------------------

    print(
        "Step 2: Calculating descriptive statistics..."
    )

    statistics = calculate_descriptive_statistics(
        df,
        column_types
    )

    print(
        f"  Statistics calculated for "
        f"{len(statistics)} columns\n"
    )

    # --------------------------------------------------------
    # Step 3
    # --------------------------------------------------------

    print(
        "Step 3: Analyzing data quality..."
    )

    quality = analyze_data_quality(
        df,
        column_types
    )

    print(
        f"  Quality score: "
        f"{quality['quality_score']}/100"
    )

    print(
        f"  Total issues: "
        f"{quality['total_issues']}\n"
    )

    # --------------------------------------------------------
    # Step 4
    # --------------------------------------------------------

    print(
        "Step 4: Analyzing distributions..."
    )

    distributions = analyze_distributions(
        df,
        column_types
    )

    print(
        f"  Distribution analysis for "
        f"{len(distributions)} columns\n"
    )

    # --------------------------------------------------------
    # Step 5
    # --------------------------------------------------------

    print(
        "Step 5: Analyzing correlations..."
    )

    correlations = analyze_correlations(
        df,
        column_types
    )

    print(
        f"  Found "
        f"{len(correlations.get('pairs', []))} "
        f"correlation pairs\n"
    )

    # --------------------------------------------------------
    # Step 6
    # --------------------------------------------------------

    print(
        "Step 6: Generating key insights..."
    )

    insights = generate_key_insights(
        df,
        column_types,
        statistics,
        quality,
        correlations,
        distributions
    )

    print(
        f"  Generated "
        f"{len(insights)} insights\n"
    )

    # --------------------------------------------------------
    # Step 7
    # --------------------------------------------------------

    print(
        "Step 7: Generating recommendations..."
    )

    recommendations = generate_recommendations(
        df,
        column_types,
        quality,
        insights
    )

    print(
        f"  High priority: "
        f"{len(recommendations['high_priority'])}"
    )

    print(
        f"  Medium priority: "
        f"{len(recommendations['medium_priority'])}"
    )

    print(
        f"  Low priority: "
        f"{len(recommendations['low_priority'])}\n"
    )

    # --------------------------------------------------------
    # Step 8
    # --------------------------------------------------------

    print(
        "Step 8: Analyzing business opportunities..."
    )

    business_opportunities = (
        analyze_business_opportunities(
            df,
            column_types
        )
    )

    print(
        f"  Available metrics: "
        f"{business_opportunities['available_metrics']}"
    )

    print(
        f"  Can calculate profit: "
        f"{business_opportunities['can_calculate_profit']}\n"
    )

    # --------------------------------------------------------
    # Step 9
    # --------------------------------------------------------

    print(
        "Step 9: Compiling executive summary..."
    )

    summary_parts = []

    summary_parts.append(
        f"The dataset contains "
        f"{len(df):,} records across "
        f"{len(df.columns)} variables."
    )

    score = quality["quality_score"]

    if score >= 90:
        summary_parts.append(
            "The overall data quality is excellent."
        )

    elif score >= 75:
        summary_parts.append(
            "The overall data quality is good."
        )

    elif score >= 50:
        summary_parts.append(
            "The overall data quality is fair, "
            "with some issues requiring attention."
        )

    else:
        summary_parts.append(
            "The overall data quality is poor "
            "and requires immediate attention."
        )

    # --------------------------------------------------------
    # Key finding
    # --------------------------------------------------------

    if insights:

        top_insight = insights[0]

        summary_parts.append(
            f"Key finding: "
            f"{top_insight['finding']}"
        )

    # --------------------------------------------------------
    # Recommendation
    # --------------------------------------------------------

    if recommendations["high_priority"]:

        top_recommendation = (
            recommendations["high_priority"][0]
        )

        summary_parts.append(
            f"Primary recommendation: "
            f"{top_recommendation['action']}"
        )

    executive_summary = " ".join(
        summary_parts
    )

    print(
        "Analysis generation complete!"
    )

    print(
        "========================================\n"
    )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    result = {
        "executive_summary": executive_summary,

        "dataset_overview": {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "memory_bytes": int(
                df.memory_usage(
                    deep=True
                ).sum()
            ),
            "column_types": column_types,
        },

        "statistics": statistics,

        "data_quality": quality,

        "distributions": distributions,

        "correlations": correlations,

        "key_insights": insights,

        "recommendations": recommendations,

        "business_opportunities": (
            business_opportunities
        ),

        "generated_at": datetime.now().isoformat(),

        "methodology": {
            "outlier_detection": (
                "IQR method "
                "(Q1 - 1.5*IQR, Q3 + 1.5*IQR)"
            ),
            "correlation_method": (
                "Pearson's correlation coefficient"
            ),
            "distribution_skewness": (
                "Fisher-Pearson coefficient of skewness"
            ),
            "quality_scoring": (
                "Penalty system based on issue severity"
            ),
            "limitations": [
                "Correlation does not imply causation.",
                (
                    "Statistical tests may assume "
                    "independent observations."
                ),
                (
                    "Business interpretations depend "
                    "on domain context."
                ),
                (
                    "Small sample sizes may limit "
                    "statistical reliability."
                ),
                (
                    "Automated column-name detection "
                    "may not identify every business concept."
                ),
            ],
        },
    }

    return to_json_safe(result)