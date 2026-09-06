from io import BytesIO
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.analysis import Analysis
from app.models.dataset import Dataset


# ============================================================
# Helpers
# ============================================================


def safe_text(value: Any) -> str:
    """
    Safely convert arbitrary values into ReportLab-compatible text.
    """
    if value is None:
        return ""

    if isinstance(value, float) and np.isnan(value):
        return ""

    return escape(str(value))


def format_number(value: Any, decimals: int = 2) -> str:
    """
    Format numeric values safely for the PDF.
    """
    try:
        number = float(value)

        if number.is_integer():
            return f"{int(number):,}"

        return f"{number:,.{decimals}f}"

    except (TypeError, ValueError):
        return str(value)


def format_percent(value: Any) -> str:
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


# ============================================================
# Dataset Loading
# ============================================================


def load_dataset(dataset: Dataset) -> pd.DataFrame:
    """
    Load the original dataset from the path stored in the database.

    The original file is read-only for report generation.
    """

    file_path = Path(dataset.file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {file_path}"
        )

    extension = dataset.file_type.lower()

    if extension == "csv":
        return pd.read_csv(file_path)

    if extension in {"xlsx", "xls"}:
        return pd.read_excel(file_path)

    raise ValueError(
        f"Unsupported dataset type: {dataset.file_type}"
    )


# ============================================================
# Chart Generation
# ============================================================


def figure_to_image(
    figure,
    width: float = 170 * mm,
) -> Image:
    """
    Convert a matplotlib figure into a ReportLab Image.
    """

    image_buffer = BytesIO()

    figure.savefig(
        image_buffer,
        format="png",
        dpi=160,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(figure)

    image_buffer.seek(0)

    image = Image(
        image_buffer,
        width=width,
        height=width * 0.55,
    )

    return image


def create_missing_values_chart(
    analysis: Analysis,
) -> Image | None:
    """
    Create a bar chart showing missing values by column.
    """

    missing_values = analysis.missing_values or {}

    rows = []

    for column, info in missing_values.items():
        if not isinstance(info, dict):
            continue

        count = info.get("count", 0)

        try:
            count = int(count)
        except (TypeError, ValueError):
            continue

        if count > 0:
            rows.append(
                (
                    str(column),
                    count,
                )
            )

    if not rows:
        return None

    rows.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    columns = [item[0] for item in rows]
    counts = [item[1] for item in rows]

    figure, axis = plt.subplots(
        figsize=(9, 4.8)
    )

    axis.bar(
        columns,
        counts,
    )

    axis.set_title(
        "Missing Values by Column",
        fontsize=14,
        fontweight="bold",
    )

    axis.set_ylabel("Missing cells")
    axis.set_xlabel("Column")

    axis.tick_params(
        axis="x",
        rotation=45,
    )

    for index, count in enumerate(counts):
        axis.text(
            index,
            count,
            str(count),
            ha="center",
            va="bottom",
            fontsize=9,
        )

    figure.tight_layout()

    return figure_to_image(figure)


def create_outlier_chart(
    analysis: Analysis,
) -> Image | None:
    """
    Create a bar chart showing detected outliers.
    """

    outliers = analysis.outliers or {}

    rows = []

    for column, value in outliers.items():

        if isinstance(value, dict):
            count = value.get(
                "count",
                value.get(
                    "outlier_count",
                    0,
                ),
            )
        else:
            count = value

        try:
            count = int(count)
        except (TypeError, ValueError):
            continue

        if count > 0:
            rows.append(
                (
                    str(column),
                    count,
                )
            )

    if not rows:
        return None

    rows.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    columns = [item[0] for item in rows]
    counts = [item[1] for item in rows]

    figure, axis = plt.subplots(
        figsize=(9, 4.8)
    )

    axis.bar(
        columns,
        counts,
    )

    axis.set_title(
        "Detected Outliers by Column",
        fontsize=14,
        fontweight="bold",
    )

    axis.set_ylabel("Outlier count")
    axis.set_xlabel("Column")

    axis.tick_params(
        axis="x",
        rotation=45,
    )

    for index, count in enumerate(counts):
        axis.text(
            index,
            count,
            str(count),
            ha="center",
            va="bottom",
            fontsize=9,
        )

    figure.tight_layout()

    return figure_to_image(figure)


def create_correlation_heatmap(
    analysis: Analysis,
) -> Image | None:
    """
    Create a correlation heatmap from stored analysis data.
    """

    correlations = analysis.correlations or {}

    if not isinstance(correlations, dict):
        return None

    if not correlations:
        return None

    try:
        correlation_df = pd.DataFrame(correlations)
    except Exception:
        return None

    if correlation_df.empty:
        return None

    correlation_df = correlation_df.apply(
        pd.to_numeric,
        errors="coerce",
    )

    correlation_df = correlation_df.dropna(
        axis=0,
        how="all",
    )

    correlation_df = correlation_df.dropna(
        axis=1,
        how="all",
    )

    if correlation_df.empty:
        return None

    figure_size = max(
        6,
        min(
            11,
            len(correlation_df.columns) * 0.7,
        ),
    )

    figure, axis = plt.subplots(
        figsize=(
            figure_size,
            figure_size * 0.75,
        )
    )

    image = axis.imshow(
        correlation_df.values,
        interpolation="nearest",
        aspect="auto",
    )

    axis.set_title(
        "Correlation Heatmap",
        fontsize=14,
        fontweight="bold",
    )

    axis.set_xticks(
        range(len(correlation_df.columns))
    )

    axis.set_xticklabels(
        correlation_df.columns,
        rotation=45,
        ha="right",
        fontsize=8,
    )

    axis.set_yticks(
        range(len(correlation_df.index))
    )

    axis.set_yticklabels(
        correlation_df.index,
        fontsize=8,
    )

    figure.colorbar(
        image,
        ax=axis,
        fraction=0.046,
        pad=0.04,
    )

    figure.tight_layout()

    return figure_to_image(
        figure,
        width=165 * mm,
    )


def create_distribution_charts(
    dataframe: pd.DataFrame,
) -> list[Image]:
    """
    Generate distribution charts for numeric columns.

    Maximum of 4 columns are shown to keep the PDF readable.
    """

    numeric_columns = list(
        dataframe.select_dtypes(
            include="number"
        ).columns
    )

    if not numeric_columns:
        return []

    charts = []

    for column in numeric_columns[:4]:

        series = dataframe[column].dropna()

        if series.empty:
            continue

        figure, axis = plt.subplots(
            figsize=(9, 4.5)
        )

        axis.hist(
            series,
            bins=20,
        )

        axis.set_title(
            f"Distribution: {column}",
            fontsize=13,
            fontweight="bold",
        )

        axis.set_xlabel(
            str(column)
        )

        axis.set_ylabel(
            "Frequency"
        )

        figure.tight_layout()

        charts.append(
            figure_to_image(figure)
        )

    return charts


# ============================================================
# Statistical Tables
# ============================================================


def build_statistics_table(
    analysis: Analysis,
) -> Table | None:
    """
    Build a readable statistical summary table.
    """

    statistics = analysis.statistics or {}

    if not isinstance(statistics, dict):
        return None

    if not statistics:
        return None

    rows = [
        [
            "Column",
            "Count",
            "Mean",
            "Std",
            "Min",
            "Max",
        ]
    ]

    for column, values in statistics.items():

        if not isinstance(values, dict):
            continue

        rows.append(
            [
                safe_text(column),
                format_number(
                    values.get(
                        "count",
                        0,
                    )
                ),
                format_number(
                    values.get(
                        "mean",
                        "-"
                    )
                ),
                format_number(
                    values.get(
                        "std",
                        "-"
                    )
                ),
                format_number(
                    values.get(
                        "min",
                        "-"
                    )
                ),
                format_number(
                    values.get(
                        "max",
                        "-"
                    )
                ),
            ]
        )

    if len(rows) == 1:
        return None

    table = Table(
        rows,
        repeatRows=1,
        colWidths=[
            35 * mm,
            20 * mm,
            25 * mm,
            25 * mm,
            25 * mm,
            25 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1f2937"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, -1),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#d1d5db"),
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#f9fafb"),
                    ],
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    return table


# ============================================================
# KPI Cards
# ============================================================


def create_kpi_table(
    dataset: Dataset,
    analysis: Analysis,
) -> Table:

    summary = analysis.summary or {}

    rows = [
        [
            "ROWS",
            "COLUMNS",
            "QUALITY SCORE",
            "MISSING CELLS",
        ],
        [
            format_number(
                summary.get(
                    "rows",
                    dataset.rows,
                )
            ),
            format_number(
                summary.get(
                    "columns",
                    dataset.columns,
                )
            ),
            f"{format_number(analysis.quality_score)}/100",
            format_number(
                summary.get(
                    "missing_cells",
                    0,
                )
            ),
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            42 * mm,
            42 * mm,
            42 * mm,
            42 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#374151"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, 0),
                    8,
                ),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, 1),
                    colors.HexColor("#f3f4f6"),
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, 1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 1),
                    (-1, 1),
                    16,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#d1d5db"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#d1d5db"),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    return table


# ============================================================
# Page Header / Footer
# ============================================================


def draw_page_header_footer(
    canvas,
    document,
):
    """
    Draw a professional header and footer on every page.
    """

    canvas.saveState()

    width, height = A4

    # Header
    canvas.setStrokeColor(
        colors.HexColor("#d1d5db")
    )

    canvas.line(
        20 * mm,
        height - 14 * mm,
        width - 20 * mm,
        height - 14 * mm,
    )

    canvas.setFont(
        "Helvetica-Bold",
        8,
    )

    canvas.setFillColor(
        colors.HexColor("#374151")
    )

    canvas.drawString(
        20 * mm,
        height - 10 * mm,
        "INSIGHTFORGE AI",
    )

    canvas.setFont(
        "Helvetica",
        8,
    )

    canvas.drawRightString(
        width - 20 * mm,
        height - 10 * mm,
        "Dataset Analysis Report",
    )

    # Footer
    canvas.line(
        20 * mm,
        13 * mm,
        width - 20 * mm,
        13 * mm,
    )

    canvas.setFont(
        "Helvetica",
        7,
    )

    canvas.setFillColor(
        colors.HexColor("#6b7280")
    )

    canvas.drawString(
        20 * mm,
        8 * mm,
        "Generated by InsightForge AI",
    )

    canvas.drawRightString(
        width - 20 * mm,
        8 * mm,
        f"Page {document.page}",
    )

    canvas.restoreState()


# ============================================================
# Report Generation
# ============================================================


def generate_analysis_report(
    dataset: Dataset,
    analysis: Analysis,
) -> BytesIO:
    """
    Generate a professional PDF analysis report.

    The report is generated from:
        1. The actual dataset
        2. Stored analysis results

    No source files are modified.
    """

    dataframe = load_dataset(dataset)

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=22 * mm,
        bottomMargin=20 * mm,
        title=(
            f"{dataset.original_filename} "
            "Analysis Report"
        ),
        author="InsightForge AI",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=25,
        leading=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#111827"),
        spaceAfter=10,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#6b7280"),
    )

    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#111827"),
        spaceBefore=8,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#374151"),
        spaceAfter=6,
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#6b7280"),
    )

    story = []

    # ========================================================
    # COVER
    # ========================================================

    story.append(Spacer(1, 35 * mm))

    story.append(
        Paragraph(
            "INSIGHTFORGE AI",
            ParagraphStyle(
                "Brand",
                parent=title_style,
                fontSize=14,
                leading=18,
                textColor=colors.HexColor("#4b5563"),
            ),
        )
    )

    story.append(Spacer(1, 10 * mm))

    story.append(
        Paragraph(
            "Dataset Analysis Report",
            title_style,
        )
    )

    story.append(
        Paragraph(
            safe_text(
                dataset.original_filename
            ),
            subtitle_style,
        )
    )

    story.append(Spacer(1, 8 * mm))

    story.append(
        HRFlowable(
            width="70%",
            thickness=1,
            color=colors.HexColor("#d1d5db"),
            hAlign="CENTER",
        )
    )

    story.append(Spacer(1, 8 * mm))

    story.append(
        Paragraph(
            (
                f"<b>Dataset ID:</b> "
                f"{dataset.id}<br/>"
                f"<b>Rows:</b> "
                f"{len(dataframe):,}<br/>"
                f"<b>Columns:</b> "
                f"{len(dataframe.columns):,}<br/>"
                f"<b>File Type:</b> "
                f"{safe_text(dataset.file_type.upper())}"
            ),
            ParagraphStyle(
                "CoverInfo",
                parent=body_style,
                alignment=TA_CENTER,
                fontSize=10,
                leading=18,
            ),
        )
    )

    story.append(Spacer(1, 15 * mm))

    story.append(
        Paragraph(
            "Automated data quality, statistical and exploratory analysis",
            subtitle_style,
        )
    )

    story.append(PageBreak())

    # ========================================================
    # EXECUTIVE SUMMARY
    # ========================================================

    story.append(
        Paragraph(
            "1. Executive Summary",
            section_style,
        )
    )

    story.append(
        Paragraph(
            safe_text(
                analysis.summary_text
                or (
                    "This report provides an automated "
                    "assessment of the uploaded dataset, "
                    "including data quality, missing values, "
                    "duplicates, outliers, statistical "
                    "properties and correlations."
                )
            ),
            body_style,
        )
    )

    story.append(Spacer(1, 5))

    story.append(
        create_kpi_table(
            dataset,
            analysis,
        )
    )

    story.append(Spacer(1, 12))

    # ========================================================
    # DATASET OVERVIEW
    # ========================================================

    story.append(
        Paragraph(
            "2. Dataset Overview",
            section_style,
        )
    )

    overview_data = [
        ["Property", "Value"],
        [
            "Dataset",
            safe_text(
                dataset.original_filename
            ),
        ],
        [
            "Rows",
            format_number(
                len(dataframe)
            ),
        ],
        [
            "Columns",
            format_number(
                len(dataframe.columns)
            ),
        ],
        [
            "File Type",
            safe_text(
                dataset.file_type.upper()
            ),
        ],
        [
            "Memory Usage",
            f"{dataframe.memory_usage(deep=True).sum() / 1024:.2f} KB",
        ],
        [
            "Numeric Columns",
            format_number(
                len(
                    dataframe.select_dtypes(
                        include="number"
                    ).columns
                )
            ),
        ],
        [
            "Categorical Columns",
            format_number(
                len(
                    dataframe.select_dtypes(
                        include=[
                            "object",
                            "category",
                            "string",
                        ]
                    ).columns
                )
            ),
        ],
    ]

    overview_table = Table(
        overview_data,
        colWidths=[
            65 * mm,
            75 * mm,
        ],
        repeatRows=1,
    )

    overview_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1f2937"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#d1d5db"),
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#f9fafb"),
                    ],
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    story.append(
        overview_table
    )

    story.append(PageBreak())

    # ========================================================
    # DATA QUALITY
    # ========================================================

    story.append(
        Paragraph(
            "3. Data Quality Analysis",
            section_style,
        )
    )

    summary = analysis.summary or {}

    story.append(
        Paragraph(
            (
                f"The dataset contains "
                f"<b>{format_number(len(dataframe))}</b> "
                f"rows and "
                f"<b>{format_number(len(dataframe.columns))}</b> "
                "columns. "
                f"The calculated data quality score is "
                f"<b>{format_number(analysis.quality_score)}/100</b>."
            ),
            body_style,
        )
    )

    # Missing values
    story.append(
        Paragraph(
            "Missing Values",
            ParagraphStyle(
                "SubHeading",
                parent=section_style,
                fontSize=12,
                leading=15,
                spaceBefore=6,
                spaceAfter=5,
            ),
        )
    )

    missing_count = summary.get(
        "missing_cells",
        0,
    )

    story.append(
        Paragraph(
            (
                f"Total missing cells: "
                f"<b>{format_number(missing_count)}</b>."
            ),
            body_style,
        )
    )

    missing_chart = create_missing_values_chart(
        analysis
    )

    if missing_chart:
        story.append(
            missing_chart
        )
        story.append(Spacer(1, 8))

    else:
        story.append(
            Paragraph(
                "No missing values were detected.",
                body_style,
            )
        )

    # Duplicate records
    story.append(
        Paragraph(
            "Duplicate Records",
            ParagraphStyle(
                "SubHeading2",
                parent=section_style,
                fontSize=12,
                leading=15,
                spaceBefore=8,
                spaceAfter=5,
            ),
        )
    )

    duplicates = analysis.duplicates or {}

    duplicate_count = duplicates.get(
        "count",
        0,
    )

    duplicate_percent = duplicates.get(
        "percent",
        0,
    )

    story.append(
        Paragraph(
            (
                f"Duplicate rows detected: "
                f"<b>{format_number(duplicate_count)}</b> "
                f"({format_percent(duplicate_percent)})."
            ),
            body_style,
        )
    )

    # ========================================================
    # OUTLIERS
    # ========================================================

    story.append(
        Paragraph(
            "4. Outlier Analysis",
            section_style,
        )
    )

    outlier_chart = create_outlier_chart(
        analysis
    )

    if outlier_chart:
        story.append(
            Paragraph(
                "Detected Outliers",
                body_style,
            )
        )

        story.append(
            outlier_chart
        )

        story.append(
            Paragraph(
                "Outliers are reported for investigation and are not automatically removed.",
                small_style,
            )
        )

    else:
        story.append(
            Paragraph(
                "No statistical outliers were detected in the analyzed numeric columns.",
                body_style,
            )
        )

    story.append(PageBreak())

    # ========================================================
    # STATISTICAL ANALYSIS
    # ========================================================

    story.append(
        Paragraph(
            "5. Statistical Analysis",
            section_style,
        )
    )

    statistics_table = build_statistics_table(
        analysis
    )

    if statistics_table:
        story.append(
            statistics_table
        )

    else:
        story.append(
            Paragraph(
                "Detailed statistical information was not available for this dataset.",
                body_style,
            )
        )

    story.append(Spacer(1, 12))

    # ========================================================
    # DISTRIBUTIONS
    # ========================================================

    distribution_charts = create_distribution_charts(
        dataframe
    )

    if distribution_charts:

        story.append(
            Paragraph(
                "Numeric Distributions",
                section_style,
            )
        )

        for chart in distribution_charts:
            story.append(
                chart
            )
            story.append(
                Spacer(1, 8)
            )

    # ========================================================
    # CORRELATION
    # ========================================================

    story.append(PageBreak())

    story.append(
        Paragraph(
            "6. Correlation Analysis",
            section_style,
        )
    )

    correlation_chart = create_correlation_heatmap(
        analysis
    )

    if correlation_chart:
        story.append(
            Paragraph(
                (
                    "The heatmap below summarizes the "
                    "pairwise relationships identified "
                    "between numeric variables."
                ),
                body_style,
            )
        )

        story.append(
            correlation_chart
        )

    else:
        story.append(
            Paragraph(
                "Correlation analysis was not available because the dataset does not contain enough numeric variables.",
                body_style,
            )
        )

    # ========================================================
    # COLUMN PROFILE
    # ========================================================

    story.append(
        Paragraph(
            "7. Column Profile",
            section_style,
        )
    )

    column_info = analysis.column_info or []

    if isinstance(column_info, list):

        column_rows = [
            [
                "Column",
                "Type",
                "Missing",
                "Unique",
            ]
        ]

        for column in column_info:

            if not isinstance(column, dict):
                continue

            column_rows.append(
                [
                    safe_text(
                        column.get(
                            "name",
                            "",
                        )
                    ),
                    safe_text(
                        column.get(
                            "dtype",
                            "",
                        )
                    ),
                    format_number(
                        column.get(
                            "missing",
                            0,
                        )
                    ),
                    format_number(
                        column.get(
                            "unique",
                            0,
                        )
                    ),
                ]
            )

        if len(column_rows) > 1:

            column_table = Table(
                column_rows,
                repeatRows=1,
                colWidths=[
                    65 * mm,
                    35 * mm,
                    25 * mm,
                    25 * mm,
                ],
            )

            column_table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.HexColor("#1f2937"),
                        ),
                        (
                            "TEXTCOLOR",
                            (0, 0),
                            (-1, 0),
                            colors.white,
                        ),
                        (
                            "FONTNAME",
                            (0, 0),
                            (-1, 0),
                            "Helvetica-Bold",
                        ),
                        (
                            "FONTSIZE",
                            (0, 0),
                            (-1, -1),
                            8,
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.4,
                            colors.HexColor("#d1d5db"),
                        ),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [
                                colors.white,
                                colors.HexColor("#f9fafb"),
                            ],
                        ),
                        (
                            "PADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                    ]
                )
            )

            story.append(
                column_table
            )

    # ========================================================
    # AI INSIGHTS
    # ========================================================

    story.append(PageBreak())

    story.append(
        Paragraph(
            "8. AI Generated Insights",
            section_style,
        )
    )

    summary_text = (
        analysis.summary_text
        or "No AI-generated insights are available."
    )

    for line in summary_text.splitlines():

        line = line.strip()

        if not line:
            continue

        story.append(
            Paragraph(
                safe_text(line),
                body_style,
            )
        )

    # ========================================================
    # CLEANING RECOMMENDATIONS
    # ========================================================

    story.append(
        Paragraph(
            "9. Cleaning Recommendations",
            section_style,
        )
    )

    recommendations = []

    if missing_count:
        recommendations.append(
            "Review missing values and apply an appropriate imputation strategy."
        )

    if duplicate_count:
        recommendations.append(
            "Review duplicate records before downstream modeling or reporting."
        )

    outliers = analysis.outliers or {}

    total_outliers = 0

    for value in outliers.values():

        if isinstance(value, dict):
            value = value.get(
                "count",
                value.get(
                    "outlier_count",
                    0,
                ),
            )

        try:
            total_outliers += int(value)
        except (TypeError, ValueError):
            pass

    if total_outliers:
        recommendations.append(
            "Investigate detected outliers and determine whether they represent valid observations or data-quality issues."
        )

    if not recommendations:
        recommendations.append(
            "No major automatic cleaning recommendations were identified from the available quality indicators."
        )

    for recommendation in recommendations:

        story.append(
            Paragraph(
                f"• {safe_text(recommendation)}",
                body_style,
            )
        )

    # ========================================================
    # FINAL ASSESSMENT
    # ========================================================

    story.append(
        Spacer(1, 10)
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=0.7,
            color=colors.HexColor("#d1d5db"),
        )
    )

    story.append(
        Spacer(1, 8)
    )

    story.append(
        Paragraph(
            "10. Final Data Health Assessment",
            section_style,
        )
    )

    quality_score = float(
        analysis.quality_score or 0
    )

    if quality_score >= 90:
        assessment = (
            "The dataset demonstrates strong overall data quality "
            "with relatively few detected quality issues."
        )

    elif quality_score >= 75:
        assessment = (
            "The dataset demonstrates acceptable data quality, "
            "although several areas may benefit from additional cleaning."
        )

    elif quality_score >= 50:
        assessment = (
            "The dataset contains notable quality issues that "
            "should be addressed before relying heavily on analytical results."
        )

    else:
        assessment = (
            "The dataset contains significant quality concerns "
            "and should undergo substantial cleaning and validation."
        )

    story.append(
        Paragraph(
            safe_text(assessment),
            body_style,
        )
    )

    story.append(
        Spacer(1, 8)
    )

    story.append(
        Paragraph(
            (
                f"<b>Final Quality Score: "
                f"{format_number(quality_score)}/100</b>"
            ),
            ParagraphStyle(
                "FinalScore",
                parent=body_style,
                fontSize=14,
                leading=18,
                alignment=TA_CENTER,
            ),
        )
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    document.build(
        story,
        onFirstPage=draw_page_header_footer,
        onLaterPages=draw_page_header_footer,
    )

    buffer.seek(0)

    return buffer