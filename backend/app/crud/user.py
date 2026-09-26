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
        file_path=dataset.file_path,
        file_type=dataset.file_type,
        file_size=dataset.file_size,
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
    dataset_id: int,
):
    dataset = get_dataset(db, dataset_id)

    if dataset:
        db.delete(dataset)
        db.commit()

    return dataset


def rename_dataset(
    db: Session,
    dataset_id: int,
    filename: str,
):
    dataset = get_dataset(db, dataset_id)

    if not dataset:
        return None

    dataset.original_filename = filename

    db.commit()
    db.refresh(dataset)

    return dataset