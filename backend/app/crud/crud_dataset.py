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


def get_cleaned_file_info(
    dataset: Dataset,
):
    """
    Check whether a cleaned version of the dataset exists.

    Examples:

        sales.csv
        sales_cleaned.csv

        sales.xlsx
        sales_cleaned.xlsx

        sales.xls
        sales_cleaned.xlsx
    """

    original_path = Path(dataset.file_path)

    if not original_path.exists():
        return {
            "cleaned_available": False,
            "cleaned_filename": None,
        }

    original_extension = original_path.suffix.lower()

    # The cleaning service converts .xls files to .xlsx.
    if original_extension == ".xls":
        cleaned_extension = ".xlsx"
    else:
        cleaned_extension = original_extension

    cleaned_path = (
        original_path.parent
        / f"{original_path.stem}_cleaned{cleaned_extension}"
    )

    if not cleaned_path.exists():
        return {
            "cleaned_available": False,
            "cleaned_filename": None,
        }

    return {
        "cleaned_available": True,
        "cleaned_filename": cleaned_path.name,
    }


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

    # -------------------------
    # Search
    # -------------------------

    if search:
        query = query.filter(
            Dataset.original_filename.ilike(
                f"%{search}%"
            )
        )

    # -------------------------
    # Sorting
    # -------------------------

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

    # -------------------------
    # Total count
    # -------------------------

    total = (
        query
        .order_by(None)
        .with_entities(
            func.count(Dataset.id)
        )
        .scalar()
    )

    # -------------------------
    # Pagination
    # -------------------------

    datasets = (
        query
        .offset(
            (page - 1) * page_size
        )
        .limit(page_size)
        .all()
    )

    # -------------------------
    # Build response items
    # -------------------------

    items = []

    for dataset in datasets:
        cleaning_info = get_cleaned_file_info(
            dataset
        )

        items.append(
            {
                "id": dataset.id,
                "owner_id": dataset.owner_id,
                "filename": dataset.filename,
                "original_filename": dataset.original_filename,
                "file_type": dataset.file_type,
                "file_size": dataset.file_size,
                "file_path": dataset.file_path,
                "rows": dataset.rows,
                "columns": dataset.columns,
                "uploaded_at": dataset.uploaded_at,
                "cleaned_available": (
                    cleaning_info[
                        "cleaned_available"
                    ]
                ),
                "cleaned_filename": (
                    cleaning_info[
                        "cleaned_filename"
                    ]
                ),
            }
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (
            ceil(total / page_size)
            if total > 0
            else 1
        ),
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
    """
    Rename the original dataset and its cleaned version.

    Example:

        Before:
            sales.csv
            sales_cleaned.csv

        Rename to:
            company_sales.csv

        After:
            company_sales.csv
            company_sales_cleaned.csv

    The database file_path is also updated so future
    downloads continue to work.
    """

    original_path = Path(
        dataset.file_path
    )

    old_stem = original_path.stem
    old_extension = original_path.suffix.lower()

    # -------------------------
    # Determine cleaned extension
    # -------------------------

    if old_extension == ".xls":
        cleaned_extension = ".xlsx"
    else:
        cleaned_extension = old_extension

    # -------------------------
    # Existing cleaned file
    # -------------------------

    old_cleaned_path = (
        original_path.parent
        / f"{old_stem}_cleaned{cleaned_extension}"
    )

    # -------------------------
    # Validate new name
    # -------------------------

    new_name = new_name.strip()

    if not new_name:
        raise ValueError(
            "Dataset name cannot be empty."
        )

    new_name_path = Path(new_name)

    # Keep the original extension if the user
    # does not provide one.
    if new_name_path.suffix:
        new_extension = (
            new_name_path.suffix
        )
    else:
        new_extension = (
            original_path.suffix
        )

    new_filename = (
        f"{new_name_path.stem}"
        f"{new_extension}"
    )

    new_original_path = (
        original_path.parent
        / new_filename
    )

    # -------------------------
    # Prevent accidental overwrite
    # -------------------------

    if (
        new_original_path != original_path
        and new_original_path.exists()
    ):
        raise ValueError(
            "A file with this name already exists."
        )

    # -------------------------
    # Rename original file
    # -------------------------

    if (
        original_path.exists()
        and original_path != new_original_path
    ):
        original_path.rename(
            new_original_path
        )

    # -------------------------
    # Rename cleaned file
    # -------------------------

    if old_cleaned_path.exists():
        new_cleaned_path = (
            new_original_path.parent
            / (
                f"{new_original_path.stem}"
                f"_cleaned"
                f"{cleaned_extension}"
            )
        )

        if (
            old_cleaned_path != new_cleaned_path
            and new_cleaned_path.exists()
        ):
            # Roll back the original rename if
            # the cleaned destination already exists.
            if new_original_path.exists():
                new_original_path.rename(
                    original_path
                )

            raise ValueError(
                "A cleaned file with this name "
                "already exists."
            )

        if (
            old_cleaned_path != new_cleaned_path
        ):
            old_cleaned_path.rename(
                new_cleaned_path
            )

    # -------------------------
    # Update database
    # -------------------------

    dataset.original_filename = new_name
    dataset.filename = new_filename
    dataset.file_path = str(
        new_original_path
    )

    db.commit()
    db.refresh(dataset)

    return dataset


def delete_dataset(
    db: Session,
    dataset: Dataset,
):
    """
    Delete the dataset, its analysis records,
    original file, and cleaned file.
    """

    # -------------------------
    # Delete analysis records
    # -------------------------

    db.query(Analysis).filter(
        Analysis.dataset_id == dataset.id
    ).delete()

    # -------------------------
    # Original file
    # -------------------------

    original_path = Path(
        dataset.file_path
    )

    if original_path.exists():
        original_path.unlink()

    # -------------------------
    # Cleaned file
    # -------------------------

    extension = (
        original_path.suffix.lower()
    )

    if extension == ".xls":
        cleaned_extension = ".xlsx"
    else:
        cleaned_extension = extension

    cleaned_path = (
        original_path.parent
        / (
            f"{original_path.stem}"
            f"_cleaned"
            f"{cleaned_extension}"
        )
    )

    if cleaned_path.exists():
        cleaned_path.unlink()

    # -------------------------
    # Delete database record
    # -------------------------

    db.delete(dataset)
    db.commit()