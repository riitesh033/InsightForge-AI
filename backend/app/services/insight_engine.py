"""
Professional Insight Engine

Converts verified analytical results into structured,
evidence-based insights.

IMPORTANT:
This module does not invent business facts.

Every insight must originate from an analytical value
already present in VerifiedAnalysisReport.
"""

from app.schemas.analysis_report import (
    CorrelationFinding,
    DescriptiveStatistics,
    OutlierFinding,
    VerifiedAnalysisReport,
)

from app.schemas.insight import (
    InsightEvidence,
    InsightReport,
    ProfessionalInsight,
)


# ============================================================
# PRIORITY HELPERS
# ============================================================

def priority_rank(priority: str) -> int:
    """
    Convert priority labels into sortable values.
    """

    ranks = {
        "Critical": 4,
        "High": 3,
        "Medium": 2,
        "Low": 1,
    }

    return ranks.get(priority, 0)


# ============================================================
# MISSING VALUE INSIGHTS
# ============================================================

def generate_missing_value_insights(
    report: VerifiedAnalysisReport,
) -> list[ProfessionalInsight]:

    insights: list[ProfessionalInsight] = []

    for item in report.data_quality.missing_values:

        if item.count <= 0:
            continue

        percentage_text = (
            f"{item.percentage:.2f}%"
            if item.percentage is not None
            else "percentage unavailable"
        )

        if (
            item.percentage is not None
            and item.percentage >= 20
        ):
            priority = "High"

        elif (
            item.percentage is not None
            and item.percentage >= 5
        ):
            priority = "Medium"

        else:
            priority = "Low"

        insights.append(
            ProfessionalInsight(
                category="Data Quality",

                title=(
                    f"Missing values detected in "
                    f"{item.column}"
                ),

                finding=(
                    f"The column '{item.column}' contains "
                    f"{item.count} missing value(s)."
                ),

                evidence=[
                    InsightEvidence(
                        metric="Missing values",
                        value=str(item.count),
                        context=item.column,
                    ),
                    InsightEvidence(
                        metric="Missing percentage",
                        value=percentage_text,
                        context=item.column,
                    ),
                ],

                interpretation=(
                    f"Missing observations are present in "
                    f"'{item.column}'. The appropriate treatment "
                    f"depends on the meaning and importance of "
                    f"this variable."
                ),

                potential_impact=(
                    "Missing observations may reduce the amount "
                    "of usable data and can affect statistical "
                    "calculations or downstream analysis if not "
                    "handled appropriately."
                ),

                recommended_action=(
                    f"Review the {item.count} missing value(s) "
                    f"in '{item.column}' and determine whether "
                    "they should be imputed, retained, or removed "
                    "based on the meaning of the field."
                ),

                priority=priority,

                confidence="High",
            )
        )

    return insights


# ============================================================
# DUPLICATE INSIGHTS
# ============================================================

def generate_duplicate_insights(
    report: VerifiedAnalysisReport,
) -> list[ProfessionalInsight]:

    insights: list[ProfessionalInsight] = []

    duplicate_data = report.data_quality.duplicates

    if duplicate_data is None:
        return insights

    if duplicate_data.count <= 0:
        return insights

    percentage_text = (
        f"{duplicate_data.percentage:.2f}%"
        if duplicate_data.percentage is not None
        else "percentage unavailable"
    )

    if (
        duplicate_data.percentage is not None
        and duplicate_data.percentage >= 10
    ):
        priority = "High"

    elif (
        duplicate_data.percentage is not None
        and duplicate_data.percentage >= 2
    ):
        priority = "Medium"

    else:
        priority = "Low"

    insights.append(
        ProfessionalInsight(
            category="Data Quality",

            title="Duplicate records detected",

            finding=(
                f"The dataset contains "
                f"{duplicate_data.count} duplicate record(s)."
            ),

            evidence=[
                InsightEvidence(
                    metric="Duplicate records",
                    value=str(
                        duplicate_data.count
                    ),
                ),
                InsightEvidence(
                    metric="Duplicate percentage",
                    value=percentage_text,
                ),
            ],

            interpretation=(
                "Duplicate records may represent repeated "
                "observations or legitimate duplicate entries. "
                "They should therefore be reviewed before removal."
            ),

            potential_impact=(
                "If duplicate records are unintended, they can "
                "cause repeated observations to receive additional "
                "weight in statistical summaries and analysis."
            ),

            recommended_action=(
                "Review the detected duplicate records and "
                "determine whether they are legitimate repeated "
                "observations or records that should be removed."
            ),

            priority=priority,

            confidence="High",
        )
    )

    return insights


# ============================================================
# OUTLIER INSIGHTS
# ============================================================

def generate_outlier_insights(
    report: VerifiedAnalysisReport,
) -> list[ProfessionalInsight]:

    insights: list[ProfessionalInsight] = []

    for item in report.outliers:

        if item.count <= 0:
            continue

        percentage_text = (
            f"{item.percentage:.2f}%"
            if item.percentage is not None
            else "percentage unavailable"
        )

        if (
            item.percentage is not None
            and item.percentage >= 10
        ):
            priority = "High"

        elif (
            item.percentage is not None
            and item.percentage >= 5
        ):
            priority = "Medium"

        else:
            priority = "Low"

        method_text = (
            item.method
            if item.method
            else "the configured outlier detection method"
        )

        insights.append(
            ProfessionalInsight(
                category="Anomaly",

                title=(
                    f"Potential outliers detected in "
                    f"{item.column}"
                ),

                finding=(
                    f"{item.count} potential outlier(s) were "
                    f"detected in '{item.column}'."
                ),

                evidence=[
                    InsightEvidence(
                        metric="Outlier count",
                        value=str(item.count),
                        context=item.column,
                    ),
                    InsightEvidence(
                        metric="Outlier percentage",
                        value=percentage_text,
                        context=item.column,
                    ),
                    InsightEvidence(
                        metric="Detection method",
                        value=method_text,
                        context=item.column,
                    ),
                ],

                interpretation=(
                    f"The values identified by {method_text} "
                    "are statistically unusual relative to the "
                    "distribution used by the detection method. "
                    "An outlier is not automatically an error."
                ),

                potential_impact=(
                    "Potential outliers can influence summary "
                    "statistics and may require review before "
                    "modeling or decision-making."
                ),

                recommended_action=(
                    f"Review the {item.count} potential outlier(s) "
                    f"in '{item.column}' and verify whether they "
                    "represent valid observations, measurement "
                    "issues, or data-entry problems."
                ),

                priority=priority,

                confidence="High",
            )
        )

    return insights


# ============================================================
# CORRELATION INSIGHTS
# ============================================================

def correlation_strength(
    coefficient: float,
) -> str:

    absolute_value = abs(coefficient)

    if absolute_value >= 0.8:
        return "very strong"

    if absolute_value >= 0.6:
        return "strong"

    if absolute_value >= 0.4:
        return "moderate"

    if absolute_value >= 0.2:
        return "weak"

    return "very weak"


def generate_correlation_insights(
    report: VerifiedAnalysisReport,
) -> list[ProfessionalInsight]:

    insights: list[ProfessionalInsight] = []

    correlations = sorted(
        report.correlations,
        key=lambda item: abs(item.coefficient),
        reverse=True,
    )

    for item in correlations:

        # Ignore weak relationships for the professional
        # insight section.
        if abs(item.coefficient) < 0.4:
            continue

        strength = correlation_strength(
            item.coefficient
        )

        direction = (
            "positive"
            if item.coefficient > 0
            else "negative"
            if item.coefficient < 0
            else "neutral"
        )

        if abs(item.coefficient) >= 0.8:
            priority = "High"
        else:
            priority = "Medium"

        insights.append(
            ProfessionalInsight(
                category="Relationship",

                title=(
                    f"{strength.capitalize()} "
                    f"{direction} relationship between "
                    f"{item.variable_a} and "
                    f"{item.variable_b}"
                ),

                finding=(
                    f"A Pearson correlation coefficient of "
                    f"{item.coefficient:.3f} was observed between "
                    f"'{item.variable_a}' and "
                    f"'{item.variable_b}'."
                ),

                evidence=[
                    InsightEvidence(
                        metric="Pearson correlation",
                        value=f"{item.coefficient:.3f}",
                        context=(
                            f"{item.variable_a} vs "
                            f"{item.variable_b}"
                        ),
                    ),
                    InsightEvidence(
                        metric="Direction",
                        value=direction,
                    ),
                    InsightEvidence(
                        metric="Strength",
                        value=strength,
                    ),
                ],

                interpretation=(
                    f"The two variables show a {strength} "
                    f"{direction} linear association in this "
                    "dataset."
                ),

                potential_impact=(
                    "The relationship may be useful for further "
                    "analysis, feature selection, or hypothesis "
                    "generation."
                ),

                recommended_action=(
                    f"Investigate the relationship between "
                    f"'{item.variable_a}' and "
                    f"'{item.variable_b}' using domain context "
                    "and additional analysis. Correlation should "
                    "not be interpreted as proof of causation."
                ),

                priority=priority,

                confidence="High",
            )
        )

    return insights


# ============================================================
# STATISTICAL INSIGHTS
# ============================================================

def generate_statistical_insights(
    report: VerifiedAnalysisReport,
) -> list[ProfessionalInsight]:

    insights: list[ProfessionalInsight] = []

    for item in report.statistics:

        if item.mean is None or item.median is None:
            continue

        if item.mean == 0:
            continue

        difference_ratio = (
            abs(item.mean - item.median)
            / abs(item.mean)
        )

        # Only report a mean/median difference when it is
        # sufficiently large to be analytically interesting.
        if difference_ratio < 0.2:
            continue

        if item.mean > item.median:

            direction = "higher"

            interpretation = (
                f"The mean is higher than the median for "
                f"'{item.column}', indicating that the average "
                "is being pulled upward relative to the median."
            )

        else:

            direction = "lower"

            interpretation = (
                f"The mean is lower than the median for "
                f"'{item.column}', indicating that the average "
                "is being pulled downward relative to the median."
            )

        insights.append(
            ProfessionalInsight(
                category="Statistics",

                title=(
                    f"Mean and median differ substantially "
                    f"for {item.column}"
                ),

                finding=(
                    f"For '{item.column}', the mean "
                    f"({item.mean:.3f}) is {direction} than "
                    f"the median ({item.median:.3f})."
                ),

                evidence=[
                    InsightEvidence(
                        metric="Mean",
                        value=f"{item.mean:.3f}",
                        context=item.column,
                    ),
                    InsightEvidence(
                        metric="Median",
                        value=f"{item.median:.3f}",
                        context=item.column,
                    ),
                ],

                interpretation=interpretation,

                potential_impact=(
                    "The difference indicates that the mean and "
                    "median represent the central tendency "
                    "differently for this variable. The median "
                    "may provide a useful complementary measure "
                    "when summarizing the distribution."
                ),

                recommended_action=(
                    f"Review the distribution of '{item.column}' "
                    "using its histogram and relevant percentile "
                    "statistics before relying on the mean alone."
                ),

                priority="Medium",

                confidence="High",
            )
        )

    return insights


# ============================================================
# MAIN ENGINE
# ============================================================

def generate_professional_insights(
    report: VerifiedAnalysisReport,
) -> InsightReport:

    insights: list[ProfessionalInsight] = []

    insights.extend(
        generate_missing_value_insights(report)
    )

    insights.extend(
        generate_duplicate_insights(report)
    )

    insights.extend(
        generate_outlier_insights(report)
    )

    insights.extend(
        generate_correlation_insights(report)
    )

    insights.extend(
        generate_statistical_insights(report)
    )

    # Highest priority first.
    insights.sort(
        key=lambda insight: priority_rank(
            insight.priority
        ),
        reverse=True,
    )

    top_findings = insights[:5]

    top_actions = insights[:5]

    return InsightReport(
        insights=insights,
        top_findings=top_findings,
        top_actions=top_actions,
    )