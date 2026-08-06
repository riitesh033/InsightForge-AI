from math import ceil
from pathlib import Path

from sqlalchemy import asc, desc, func
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
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
    sort_by: str = "uploaded_at",
    order: str = "desc",
):
    query = (
        db.query(Dataset)
        .filter(
            Dataset.owner_id == owner_id
        )
    )

    # Search
    if search:
        query = query.filter(
            Dataset.original_filename.ilike(
                f"%{search}%"
            )
        )

    # Sorting
    sortable_columns = {
        "uploaded_at": Dataset.uploaded_at,
        "rows": Dataset.rows,
        "columns": Dataset.columns,
        "file_size": Dataset.file_size,
        "original_filename": Dataset.original_filename,
    }

    sort_column = sortable_columns.get(
        sort_by,
        Dataset.uploaded_at,
    )

    if order.lower() == "asc":
        query = query.order_by(
            asc(sort_column)
        )
    else:
        query = query.order_by(
            desc(sort_column)
        )


    # Count BEFORE pagination and remove ordering
    total = (
        query
        .order_by(None)
        .with_entities(
            func.count(Dataset.id)
        )
        .scalar()
    )


    datasets = (
        query
        .offset(
            (page - 1) * page_size
        )
        .limit(page_size)
        .all()
    )


    return {
        "items": datasets,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": ceil(total / page_size)
        if total > 0
        else 1,
    }



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

    db.query(Analysis).filter(
        Analysis.dataset_id == dataset.id
    ).delete()


    file_path = Path(
        dataset.file_path
    )

    if file_path.exists():
        file_path.unlink()


    db.delete(dataset)

    db.commit()