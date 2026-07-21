from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.schemas.dataset import DatasetCreate


def create_dataset(
    db: Session,
    dataset: DatasetCreate,
):
    db_dataset = Dataset(
        filename=dataset.filename,
        original_filename=dataset.original_filename,
        file_type=dataset.file_type,
        file_size=dataset.file_size,
        file_path=dataset.file_path,
        rows=dataset.rows,
        columns=dataset.columns,
        owner_id=dataset.owner_id,
    )

    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)

    return db_dataset


def get_datasets(
    db: Session,
):
    return (
        db.query(Dataset)
        .order_by(Dataset.uploaded_at.desc())
        .all()
    )


def get_dataset(
    db: Session,
    dataset_id: int,
):
    return (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id)
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
    db.delete(dataset)
    db.commit()