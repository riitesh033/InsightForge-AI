"""
Verified Analysis Mapper

Converts the existing Analysis database object into the
structured VerifiedAnalysisReport schema.

IMPORTANT:
This module does NOT invent findings, recommendations,
business outcomes, or interpretations.

It only normalizes already-calculated analytical results.
"""

from typing import Any

from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.schemas.analysis_report import (
    ColumnInfoReport,
    CorrelationFinding,
    DataQualityReport,
    DescriptiveStatistics,
    DatasetReportInfo,
    DuplicateReport,
    MissingValueReport,
    OutlierFinding,
    VerifiedAnalysisReport,
)


# ============================================================
# SAFE CONVERSION HELPERS
# ============================================================

def safe_int(
    value: Any,
    default: int | None = None,
) -> int | None:
    """Safely convert a value to int."""

    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(
    value: Any,
    default: float | None = None,
) -> float | None:
    """Safely convert a value to float."""

    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_string(
    value: Any,
    default: str | None = None,
) -> str | None:
    """Safely convert a value to string."""

    if value is None:
        return default

    return str(value)


def first_not_none(*values: Any) -> Any:
    """
    Return the first value that is not None.

    Unlike using `or`, this preserves legitimate values
    such as 0 and 0.0.
    """

    for value in values:
        if value is not None:
            return value

    return None


# ============================================================
# DATASET INFORMATION
# ============================================================

def build_dataset_info(
    dataset: Dataset,
) -> DatasetReportInfo:
    """
    Convert Dataset model information into report metadata.
    """

    return DatasetReportInfo(
        dataset_id=dataset.id,
        filename=dataset.original_filename,
        file_type=dataset.file_type,
        rows=safe_int(dataset.rows, 0) or 0,
        columns=safe_int(dataset.columns, 0) or 0,
    )


# ============================================================
# COLUMN INFORMATION
# ============================================================

def build_column_info(
    analysis: Analysis,
) -> list[ColumnInfoReport]:
    """
    Normalize the existing column_info structure.

    The existing analysis may store column information as either:

        {
            "Sales": {
                "dtype": "float64",
                "unique": 100,
                "missing": 2
            }
        }

    or:

        [
            {
                "name": "Sales",
                "dtype": "float64",
                "unique": 100,
                "missing": 2
            }
        ]

    This function only normalizes already-calculated values.
    """

    raw = analysis.column_info

    if raw is None:
        return []

    if isinstance(raw, list):
        items = raw

    elif isinstance(raw, dict):
        items = []

        for name, value in raw.items():

            if isinstance(value, dict):
                items.append(
                    {
                        "name": name,
                        **value,
                    }
                )

    else:
        return []

    result: list[ColumnInfoReport] = []

    for item in items:

        if not isinstance(item, dict):
            continue

        name = first_not_none(
            item.get("name"),
            item.get("column"),
            item.get("column_name"),
        )

        if not isinstance(name, str):
            continue

        dtype = first_not_none(
            item.get("dtype"),
            item.get("data_type"),
            item.get("type"),
        )

        unique = first_not_none(
            item.get("unique"),
            item.get("unique_count"),
        )

        missing = first_not_none(
            item.get("missing"),
            item.get("missing_count"),
        )

        missing_percentage = first_not_none(
            item.get("missing_percent"),
            item.get("missing_percentage"),
        )

        memory_usage = item.get("memory_usage")

        result.append(
            ColumnInfoReport(
                name=name,
                dtype=safe_string(dtype) or "",
                unique=safe_int(unique, 0) or 0,
                missing=safe_int(missing, 0) or 0,
                missing_percentage=safe_float(
                    missing_percentage
                ),
                memory_usage=safe_int(
                    memory_usage
                ),
            )
        )

    return result


# ============================================================
# MISSING VALUES
# ============================================================

def build_missing_values(
    missing_values: Any,
) -> list[MissingValueReport]:
    """
    Normalize the existing missing_values structure.

    Existing analysis may store missing values as:

        {
            "Column A": 10,
            "Column B": 5
        }

    or:

        {
            "Column A": {
                "count": 10,
                "percentage": 2.5
            }
        }
    """

    if not isinstance(missing_values, dict):
        return []

    result: list[MissingValueReport] = []

    for column, value in missing_values.items():

        count = 0
        percentage = None

        if isinstance(value, dict):

            count = safe_int(
                value.get("count"),
                0,
            ) or 0

            percentage = safe_float(
                first_not_none(
                    value.get("percentage"),
                    value.get("percent"),
                    value.get("missing_percentage"),
                )
            )

        else:

            count = safe_int(
                value,
                0,
            ) or 0

        result.append(
            MissingValueReport(
                column=str(column),
                count=count,
                percentage=percentage,
            )
        )

    return result


# ============================================================
# DUPLICATES
# ============================================================

def build_duplicate_report(
    duplicates: Any,
) -> DuplicateReport | None:
    """
    Normalize duplicate-row information.
    """

    if duplicates is None:
        return None

    if isinstance(duplicates, dict):

        count = safe_int(
            first_not_none(
                duplicates.get("count"),
                duplicates.get("duplicate_count"),
                duplicates.get("duplicates"),
            ),
            0,
        ) or 0

        percentage = safe_float(
            first_not_none(
                duplicates.get("percentage"),
                duplicates.get("percent"),
                duplicates.get("duplicate_percentage"),
            )
        )

        return DuplicateReport(
            count=count,
            percentage=percentage,
        )

    count = safe_int(
        duplicates,
        0,
    ) or 0

    return DuplicateReport(
        count=count,
        percentage=None,
    )


# ============================================================
# DATA QUALITY
# ============================================================

def build_data_quality(
    analysis: Analysis,
) -> DataQualityReport:
    """
    Convert existing data-quality information.

    The mapper uses the existing quality score and detected
    missing/duplicate information.

    It does not create new quality issues.
    """

    missing_values = build_missing_values(
        analysis.missing_values
    )

    duplicates = build_duplicate_report(
        analysis.duplicates
    )

    return DataQualityReport(
        quality_score=safe_float(
            analysis.quality_score
        ),
        missing_values=missing_values,
        duplicates=duplicates,
        invalid_values=[],
        datatype_issues=[],
        inconsistent_values=[],
    )


# ============================================================
# DESCRIPTIVE STATISTICS
# ============================================================

def build_statistics(
    statistics: Any,
) -> list[DescriptiveStatistics]:
    """
    Convert the existing statistics dictionary into
    a list of DescriptiveStatistics objects.
    """

    if not isinstance(statistics, dict):
        return []

    result: list[DescriptiveStatistics] = []

    for column, values in statistics.items():

        if not isinstance(values, dict):
            continue

        result.append(
            DescriptiveStatistics(
                column=str(column),

                count=safe_int(
                    values.get("count")
                ),

                mean=safe_float(
                    values.get("mean")
                ),

                median=safe_float(
                    values.get("median")
                ),

                mode=(
                    values.get("mode")
                    if values.get("mode") is not None
                    else None
                ),

                minimum=safe_float(
                    first_not_none(
                        values.get("min"),
                        values.get("minimum"),
                    )
                ),

                maximum=safe_float(
                    first_not_none(
                        values.get("max"),
                        values.get("maximum"),
                    )
                ),

                range=safe_float(
                    values.get("range")
                ),

                standard_deviation=safe_float(
                    first_not_none(
                        values.get("std"),
                        values.get("standard_deviation"),
                    )
                ),

                variance=safe_float(
                    values.get("variance")
                ),

                q1=safe_float(
                    first_not_none(
                        values.get("q1"),
                        values.get("Q1"),
                    )
                ),

                q3=safe_float(
                    first_not_none(
                        values.get("q3"),
                        values.get("Q3"),
                    )
                ),

                iqr=safe_float(
                    values.get("iqr")
                ),

                skewness=safe_float(
                    values.get("skewness")
                ),

                kurtosis=safe_float(
                    values.get("kurtosis")
                ),

                percentile_5=safe_float(
                    first_not_none(
                        values.get("percentile_5"),
                        values.get("5th_percentile"),
                    )
                ),

                percentile_95=safe_float(
                    first_not_none(
                        values.get("percentile_95"),
                        values.get("95th_percentile"),
                    )
                ),

                coefficient_of_variation=safe_float(
                    first_not_none(
                        values.get("coefficient_of_variation"),
                        values.get("cv"),
                    )
                ),
            )
        )

    return result


# ============================================================
# CORRELATIONS
# ============================================================

def build_correlations(
    correlations: Any,
) -> list[CorrelationFinding]:
    """
    Convert the existing correlation matrix into
    pairwise correlation findings.

    Only actual numeric correlation coefficients are included.
    """

    if not isinstance(correlations, dict):
        return []

    result: list[CorrelationFinding] = []

    # The existing system stores the correlation matrix
    # as a dictionary of columns.
    #
    # Example:
    #
    # {
    #     "Sales": {
    #         "Sales": 1.0,
    #         "Profit": 0.82
    #     },
    #     "Profit": {
    #         "Sales": 0.82,
    #         "Profit": 1.0
    #     }
    # }

    columns = list(correlations.keys())

    for index, column_a in enumerate(columns):

        values_a = correlations.get(column_a)

        if not isinstance(values_a, dict):
            continue

        for column_b in columns[index + 1:]:

            coefficient = values_a.get(column_b)

            coefficient = safe_float(
                coefficient
            )

            if coefficient is None:
                continue

            if coefficient < -1 or coefficient > 1:
                continue

            if coefficient > 0:
                direction = "positive"
            elif coefficient < 0:
                direction = "negative"
            else:
                direction = "neutral"

            result.append(
                CorrelationFinding(
                    variable_a=str(column_a),
                    variable_b=str(column_b),
                    coefficient=coefficient,
                    method="pearson",
                    direction=direction,
                )
            )

    return result


# ============================================================
# OUTLIERS
# ============================================================

def build_outliers(
    outliers: Any,
) -> list[OutlierFinding]:
    """
    Convert the existing outlier results into a structured list.
    """

    if not isinstance(outliers, dict):
        return []

    result: list[OutlierFinding] = []

    for column, value in outliers.items():

        count = 0
        percentage = None
        method = None
        lower_bound = None
        upper_bound = None

        if isinstance(value, dict):

            count = safe_int(
                first_not_none(
                    value.get("count"),
                    value.get("outlier_count"),
                ),
                0,
            ) or 0

            percentage = safe_float(
                first_not_none(
                    value.get("percentage"),
                    value.get("percent"),
                    value.get("outlier_percentage"),
                )
            )

            method = safe_string(
                value.get("method")
            )

            lower_bound = safe_float(
                first_not_none(
                    value.get("lower_bound"),
                    value.get("lower"),
                )
            )

            upper_bound = safe_float(
                first_not_none(
                    value.get("upper_bound"),
                    value.get("upper"),
                )
            )

        else:

            count = safe_int(
                value,
                0,
            ) or 0

        result.append(
            OutlierFinding(
                column=str(column),
                count=count,
                percentage=percentage,
                method=method,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
            )
        )

    return result


# ============================================================
# MAIN MAPPER
# ============================================================

def build_verified_analysis_report(
    analysis: Analysis,
    dataset: Dataset,
) -> VerifiedAnalysisReport:
    """
    Build the complete verified analysis contract.

    This function is intentionally deterministic.

    It does NOT:
        - generate recommendations
        - infer business impact
        - invent trends
        - claim causation
        - ask an LLM to interpret the data

    It only maps already-calculated analysis results.
    """

    return VerifiedAnalysisReport(

        # ----------------------------------------------------
        # Dataset information
        # ----------------------------------------------------

        dataset=build_dataset_info(
            dataset
        ),

        # ----------------------------------------------------
        # Column information
        # ----------------------------------------------------

        column_info=build_column_info(
            analysis
        ),

        # ----------------------------------------------------
        # Data quality
        # ----------------------------------------------------

        data_quality=build_data_quality(
            analysis
        ),

        # ----------------------------------------------------
        # Descriptive statistics
        # ----------------------------------------------------

        statistics=build_statistics(
            analysis.statistics
        ),

        # ----------------------------------------------------
        # Correlations
        # ----------------------------------------------------

        correlations=build_correlations(
            analysis.correlations
        ),

        # ----------------------------------------------------
        # Outliers
        # ----------------------------------------------------

        outliers=build_outliers(
            analysis.outliers
        ),

        # ----------------------------------------------------
        # Temporal analysis
        # ----------------------------------------------------
        #
        # Intentionally empty for now.
        #
        # A date range alone does not prove a trend.
        # Temporal trend detection should only be added when
        # the underlying analysis explicitly calculates it.
        #

        temporal_analysis=[],
    )
