from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.models.analysis import Analysis


def generate_analysis_report(
    analysis: Analysis,
) -> BytesIO:

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]

    heading_style = styles["Heading2"]

    body_style = styles["BodyText"]

    story = []

    # =========================
    # Title
    # =========================

    story.append(
        Paragraph(
            "InsightForge AI - Dataset Analysis Report",
            title_style,
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            f"Dataset ID: {analysis.dataset_id}",
            body_style,
        )
    )

    story.append(
        Paragraph(
            f"Analysis ID: {analysis.id}",
            body_style,
        )
    )

    story.append(Spacer(1, 15))

    # =========================
    # Quality Score
    # =========================

    story.append(
        Paragraph(
            "Data Quality Score",
            heading_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>{analysis.quality_score}/100</b>",
            body_style,
        )
    )

    story.append(Spacer(1, 12))

    # =========================
    # Dataset Summary
    # =========================

    story.append(
        Paragraph(
            "Dataset Summary",
            heading_style,
        )
    )

    summary = analysis.summary or {}

    summary_data = [
        ["Metric", "Value"],
        [
            "Rows",
            str(summary.get("rows", 0)),
        ],
        [
            "Columns",
            str(summary.get("columns", 0)),
        ],
        [
            "Missing Cells",
            str(summary.get("missing_cells", 0)),
        ],
        [
            "Duplicate Rows",
            str(summary.get("duplicate_rows", 0)),
        ],
    ]

    table = Table(
        summary_data,
        colWidths=[70 * mm, 70 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.grey,
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
                    0.5,
                    colors.grey,
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(table)

    story.append(Spacer(1, 15))

    # =========================
    # Missing Values
    # =========================

    story.append(
        Paragraph(
            "Missing Values",
            heading_style,
        )
    )

    missing_values = analysis.missing_values or {}

    missing_data = [
        ["Column", "Count", "Percentage"]
    ]

    for column, info in missing_values.items():

        if not isinstance(info, dict):
            continue

        missing_data.append(
            [
                str(column),
                str(info.get("count", 0)),
                f"{float(info.get('percent', 0)):.2f}%",
            ]
        )

    if len(missing_data) == 1:
        missing_data.append(
            ["No missing values", "0", "0%"]
        )

    missing_table = Table(
        missing_data,
        colWidths=[
            70 * mm,
            35 * mm,
            35 * mm,
        ],
    )

    missing_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.grey,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(missing_table)

    story.append(Spacer(1, 15))

    # =========================
    # Duplicates
    # =========================

    story.append(
        Paragraph(
            "Duplicate Records",
            heading_style,
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
            f"Duplicate rows: <b>{duplicate_count}</b>",
            body_style,
        )
    )

    story.append(
        Paragraph(
            f"Duplicate percentage: "
            f"<b>{float(duplicate_percent):.2f}%</b>",
            body_style,
        )
    )

    story.append(Spacer(1, 15))

    # =========================
    # Outliers
    # =========================

    story.append(
        Paragraph(
            "Outlier Detection",
            heading_style,
        )
    )

    outliers = analysis.outliers or {}

    if outliers:

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

            story.append(
                Paragraph(
                    f"{column}: {count} outliers",
                    body_style,
                )
            )

    else:

        story.append(
            Paragraph(
                "No outliers detected.",
                body_style,
            )
        )

    story.append(Spacer(1, 15))

    # =========================
    # AI Insights
    # =========================

    story.append(
        Paragraph(
            "AI Generated Insights",
            heading_style,
        )
    )

    summary_text = (
        analysis.summary_text
        or "No AI insights available."
    )

    # Preserve line breaks from AI output
    for line in summary_text.splitlines():

        if line.strip():

            story.append(
                Paragraph(
                    line.strip(),
                    body_style,
                )
            )

            story.append(
                Spacer(1, 4)
            )

    # =========================
    # Build PDF
    # =========================

    document.build(story)

    buffer.seek(0)

    return buffer