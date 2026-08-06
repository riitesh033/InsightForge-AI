from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.dataset import Dataset


def get_analysis(
    db: Session,
    dataset_id: int,
    owner_id: int,
):

    return (
        db.query(Analysis)
        .join(Dataset)
        .filter(
            Analysis.dataset_id == dataset_id,
            Dataset.owner_id == owner_id,
        )
        .first()
    )