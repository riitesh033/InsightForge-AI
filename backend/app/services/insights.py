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