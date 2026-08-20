from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.dataset import Dataset


def get_dataset_context(
    db: Session,
    dataset_id: int,
    user_id: int,
):
    dataset = (
        db.query(Dataset)
        .filter(
            Dataset.id == dataset_id,
            Dataset.owner_id == user_id,
        )
        .first()
    )

    if dataset is None:
        return None

    analysis = (
        db.query(Analysis)
        .filter(
            Analysis.dataset_id == dataset_id,
        )
        .first()
    )

    if analysis is None:
        return {
            "dataset": dataset,
            "analysis": None,
        }

    return {
        "dataset": dataset,
        "analysis": analysis,
    }

def generate_chat_answer(
    question: str,
    context: dict,
) -> str:

    dataset = context["dataset"]
    analysis = context["analysis"]

    if analysis is None:
        return (
            "I found the dataset, but its analysis "
            "is not available yet."
        )

    question_lower = question.lower()

    if "missing" in question_lower:
        missing_values = analysis.missing_values or {}

        total_missing = sum(
            int(value.get("count", 0))
            for value in missing_values.values()
            if isinstance(value, dict)
        )

        return (
            f"The dataset contains {total_missing} "
            "missing values in total."
        )

    if "duplicate" in question_lower:
        duplicates = analysis.duplicates or {}

        count = duplicates.get("count", 0)

        return (
            f"The dataset contains {count} "
            "duplicate records."
        )

    if "quality" in question_lower:
        return (
            f"The current data quality score is "
            f"{analysis.quality_score}/100."
        )

    return (
        f"I analyzed '{dataset.original_filename}'. "
        f"It contains {dataset.rows} rows and "
        f"{dataset.columns} columns. "
        f"Your question was: '{question}'"
    )