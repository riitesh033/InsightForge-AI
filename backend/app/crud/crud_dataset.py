from pathlib import Path

from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.dataset import Dataset


def create_dataset(
    db: Session,
    dataset: Dataset,
):
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset


def get_datasets(
    db: Session,
    owner_id: int,
):
    return (
        db.query(Dataset)
        .filter(Dataset.owner_id == owner_id)
        .order_by(Dataset.uploaded_at.desc())
        .all()
    )


def get_dataset(
    db: Session,
    dataset_id: int,
    owner_id: int,
):
    return (
        db.query(Dataset)
        .filter(
            Dataset.id == dataset_id,
            Dataset.owner_id == owner_id,
        )
        .first()
    )


def rename_dataset(
    db: Session,
    dataset: Dataset,
    new_name: str,
):
    dataset.original_filename = new_name

    db.commit()
    db.refresh(dataset)

    return dataset


def delete_dataset(
    db: Session,
    dataset: Dataset,
):
    # Delete analysis record
    (
        db.query(Analysis)
        .filter(
            Analysis.dataset_id == dataset.id
        )
        .delete()
    )

    # Delete uploaded file
    file_path = Path(dataset.file_path)

    if file_path.exists():
        file_path.unlink()

    # Delete dataset
    db.delete(dataset)

    db.commit()