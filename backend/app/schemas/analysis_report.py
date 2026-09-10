from typing import Any

from pydantic import BaseModel, Field


# ============================================================
# DATASET INFORMATION
# ============================================================

class DatasetReportInfo(BaseModel):
    """
    Basic verified information about the analyzed dataset.
    """

    dataset_id: int | None = None
    filename: str | None = None
    file_type: str | None = None

    rows: int = 0
    columns: int = 0


# ============================================================
# COLUMN INFORMATION
# ============================================================

class ColumnInfoReport(BaseModel):
    """
    Verified information about an individual dataset column.
    """

    name: str

    dtype: str

    unique: int = Field(
        default=0,
        ge=0,
    )

    missing: int = Field(
        default=0,
        ge=0,
    )

    missing_percentage: float | None = Field(
        default=None,
        ge=0,
    )

    memory_usage: int | None = Field(
        default=None,
        ge=0,
    )


# ============================================================
# DATA QUALITY
# ============================================================

class MissingValueReport(BaseModel):
    """
    Verified missing-value information for one column.
    """

    column: str

    count: int = Field(
        default=0,
        ge=0,
    )

    percentage: float | None = Field(
        default=None,
        ge=0,
    )


class DuplicateReport(BaseModel):
    """
    Verified duplicate-record information.
    """

    count: int = Field(
        default=0,
        ge=0,
    )

    percentage: float | None = Field(
        default=None,
        ge=0,
    )


class DataQualityReport(BaseModel):
    """
    Verified data-quality measurements.
    """

    quality_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    missing_values: list[MissingValueReport] = Field(
        default_factory=list,
    )

    duplicates: DuplicateReport | None = None

    invalid_values: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    datatype_issues: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    inconsistent_values: list[dict[str, Any]] = Field(
        default_factory=list,
    )


# ============================================================
# DESCRIPTIVE STATISTICS
# ============================================================

class DescriptiveStatistics(BaseModel):
    """
    Verified descriptive statistics for one numerical column.
    """

    column: str

    count: int | None = None

    mean: float | None = None

    median: float | None = None

    mode: float | str | None = None

    minimum: float | None = None

    maximum: float | None = None

    range: float | None = None

    standard_deviation: float | None = None

    variance: float | None = None

    q1: float | None = None

    q3: float | None = None

    iqr: float | None = None

    skewness: float | None = None

    kurtosis: float | None = None

    percentile_5: float | None = None

    percentile_95: float | None = None

    coefficient_of_variation: float | None = None


# ============================================================
# CORRELATIONS
# ============================================================

class CorrelationFinding(BaseModel):
    """
    A verified relationship between two numerical variables.
    """

    variable_a: str

    variable_b: str

    coefficient: float = Field(
        ge=-1,
        le=1,
    )

    method: str = "pearson"

    direction: str | None = None


# ============================================================
# OUTLIERS
# ============================================================

class OutlierFinding(BaseModel):
    """
    Verified statistical outlier information.
    """

    column: str

    count: int = Field(
        default=0,
        ge=0,
    )

    percentage: float | None = Field(
        default=None,
        ge=0,
    )

    method: str | None = None

    lower_bound: float | None = None

    upper_bound: float | None = None


# ============================================================
# TEMPORAL ANALYSIS
# ============================================================

class TemporalFinding(BaseModel):
    """
    Verified temporal information.

    A trend should only be populated when the analysis engine
    has actually calculated and verified it.
    """

    date_column: str

    minimum_date: str | None = None

    maximum_date: str | None = None

    time_span_days: int | None = None

    trend_direction: str | None = None

    period_values: list[dict[str, Any]] = Field(
        default_factory=list,
    )


# ============================================================
# COMPLETE VERIFIED ANALYSIS
# ============================================================

class VerifiedAnalysisReport(BaseModel):
    """
    Master contract for the professional analytical report.

    Every value entering the report should come from verified
    analytical results rather than being invented by an LLM.
    """

    dataset: DatasetReportInfo

    data_quality: DataQualityReport

    column_info: list[ColumnInfoReport] = Field(
        default_factory=list,
    )

    statistics: list[DescriptiveStatistics] = Field(
        default_factory=list,
    )

    correlations: list[CorrelationFinding] = Field(
        default_factory=list,
    )

    outliers: list[OutlierFinding] = Field(
        default_factory=list,
    )

    temporal_analysis: list[TemporalFinding] = Field(
        default_factory=list,
    )