from typing import Any


def generate_dataset_summary(
    analysis: dict[str, Any],
) -> str:
    summary = analysis["summary"]

    rows = summary["rows"]
    columns = summary["columns"]
    memory = summary["memory_usage"]
    missing = summary["missing_cells"]
    duplicates = summary["duplicate_rows"]

    text = []

    text.append(
        f"The dataset contains {rows:,} rows and {columns} columns."
    )

    text.append(
        f"It occupies approximately {memory / 1024:.2f} KB of memory."
    )

    if missing == 0:
        text.append(
            "No missing values were detected."
        )
    else:
        text.append(
            f"There are {missing} missing values in the dataset."
        )

    if duplicates == 0:
        text.append(
            "No duplicate rows were found."
        )
    else:
        text.append(
            f"{duplicates} duplicate rows were detected."
        )

    return " ".join(text)


def calculate_quality_score(
    analysis: dict[str, Any],
) -> int:
    """
    Calculate a quality score between 0 and 100.
    """

    summary = analysis["summary"]

    rows = max(summary["rows"], 1)
    missing = summary["missing_cells"]
    duplicates = summary["duplicate_rows"]

    outlier_count = sum(
        analysis["outliers"].values()
    )

    score = 100

    # Missing values penalty (40%)
    score -= int((missing / rows) * 40)

    # Duplicate rows penalty (30%)
    score -= int((duplicates / rows) * 30)

    # Outlier penalty (30%)
    score -= int((outlier_count / rows) * 30)

    return max(score, 0)