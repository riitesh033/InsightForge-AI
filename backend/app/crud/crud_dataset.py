from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.schemas.dataset import DatasetCreate


def create_dataset(
    db: Session,
    dataset: DatasetCreate,
) -> Dataset:
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


def get_dataset(
    db: Session,
    dataset_id: int,
):
    return (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id)
        .first()
    )


def get_user_datasets(
    db: Session,
    owner_id: int,
):
    return (
        db.query(Dataset)
        .filter(Dataset.owner_id == owner_id)
        .order_by(Dataset.uploaded_at.desc())
        .all()
    )


def delete_dataset(
    db: Session,
    dataset: Dataset,
):
    db.delete(dataset)
    db.commit()