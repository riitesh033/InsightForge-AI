from math import ceil
from pathlib import Path
import logging

from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.dataset import Dataset
from app.services.dataset_storage import (
    build_cloud_storage_id,
    delete_dataset_storage,
    is_cloud_dataset,
    resolve_dataset_path,
)
from app.services.cloud_storage import supabase_storage

logger = logging.getLogger(__name__)


def create_dataset(
    db: Session,
    dataset: Dataset,
):
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset


def _build_cleaned_storage_id(dataset_id: int) -> str:
    return build_cloud_storage_id(
        f"{dataset_id}/cleaned"
    )


def get_cleaned_file_info(
    dataset: Dataset,
):
    """
    Check whether a cleaned version of the dataset exists.

    Local datasets:
        original_name_cleaned.extension

    Supabase datasets:
        datasets/<dataset_id>/cleaned
    """

    # Cloud dataset
    if is_cloud_dataset(dataset.file_path):
        cleaned_storage_id = _build_cleaned_storage_id(
            dataset.id
        )

        try:
            manifest = supabase_storage.get_manifest(
                cleaned_storage_id
            )

            chunks = manifest.get("chunks", [])

            if not chunks:
                return {
                    "cleaned_available": False,
                    "cleaned_filename": None,
                }

            original_extension = (
                Path(dataset.original_filename)
                .suffix
                .lower()
            )

            if original_extension == ".xls":
                cleaned_extension = ".xlsx"
            else:
                cleaned_extension = original_extension

            original_stem = Path(
                dataset.original_filename
            ).stem

            cleaned_filename = (
                f"{original_stem}_cleaned"
                f"{cleaned_extension}"
            )

            return {
                "cleaned_available": True,
                "cleaned_filename": cleaned_filename,
            }

        except (
            FileNotFoundError,
            RuntimeError,
            ValueError,
        ):
            return {
                "cleaned_available": False,
                "cleaned_filename": None,
            }

    # Local dataset
    try:
        original_path = resolve_dataset_path(
            dataset.file_path
        )
    except ValueError:
        return {
            "cleaned_available": False,
            "cleaned_filename": None,
        }

    if not original_path.is_file():
        return {
            "cleaned_available": False,
            "cleaned_filename": None,
        }

    original_extension = (
        Path(dataset.original_filename).suffix.lower()
    )

    # .xls files are converted to .xlsx during cleaning
    if original_extension == ".xls":
        cleaned_extension = ".xlsx"
    else:
        cleaned_extension = original_extension

    cleaned_filename = (
        f"{Path(dataset.original_filename).stem}_cleaned"
        f"{cleaned_extension}"
    )
    cleaned_path = (
        original_path.parent
        / cleaned_filename
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
        .filter(Dataset.owner_id == owner_id)
    )

    if search:
        query = query.filter(
            Dataset.original_filename.ilike(
                f"%{search}%"
            )
        )

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

    total = (
        query
        .order_by(None)
        .with_entities(func.count(Dataset.id))
        .scalar()
    )

    datasets = (
        query
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

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
                "cleaned_available": cleaning_info[
                    "cleaned_available"
                ],
                "cleaned_filename": cleaning_info[
                    "cleaned_filename"
                ],
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

    Local datasets are physically renamed.

    Cloud datasets keep their Supabase storage identifier
    because the database stores the logical storage location,
    not the original filename.
    """

    requested_name = Path(
        new_name.replace("\\", "/").rsplit("/", 1)[-1]
    )

    if requested_name.suffix:
        new_extension = requested_name.suffix
    else:
        new_extension = Path(
            dataset.original_filename
        ).suffix

    new_filename = (
        f"{requested_name.stem}"
        f"{new_extension}"
    )

    # Cloud dataset
    if is_cloud_dataset(dataset.file_path):
        dataset.original_filename = new_name
        dataset.filename = new_filename

        db.commit()
        db.refresh(dataset)

        return dataset

    # Local dataset
    original_path = resolve_dataset_path(
        dataset.file_path
    )

    old_extension = Path(
        dataset.original_filename
    ).suffix.lower()

    # Cleaning converts .xls -> .xlsx
    if old_extension == ".xls":
        cleaned_extension = ".xlsx"
    else:
        cleaned_extension = old_extension

    old_cleaned_path = (
        original_path.parent
        / f"{Path(dataset.original_filename).stem}_cleaned"
        f"{cleaned_extension}"
    )

    new_original_path = (
        original_path.parent
        / new_filename
    )

    # Rename original physical file
    if (
        original_path.exists()
        and original_path != new_original_path
    ):
        original_path.rename(
            new_original_path
        )

    # Rename cleaned physical file
    if old_cleaned_path.exists():
        new_cleaned_path = (
            new_original_path.parent
            / f"{new_original_path.stem}"
            f"_cleaned"
            f"{cleaned_extension}"
        )

        if (
            old_cleaned_path
            != new_cleaned_path
        ):
            old_cleaned_path.rename(
                new_cleaned_path
            )

    # Update database record
    dataset.original_filename = new_name
    dataset.filename = new_filename
    dataset.file_path = new_filename

    db.commit()
    db.refresh(dataset)

    return dataset


def delete_dataset(
    db: Session,
    dataset: Dataset,
):
    """
    Delete the dataset, its analysis,
    original file, and cleaned file.

    Cloud datasets additionally remove their
    Supabase storage objects.
    """

    # Delete analysis records
    db.query(Analysis).filter(
        Analysis.dataset_id == dataset.id
    ).delete()

    # Delete chat sessions (and their messages) before removing the
    # dataset so no chat session is left pointing at a dataset that no
    # longer exists. Messages are removed explicitly rather than relying
    # on the database-level ON DELETE CASCADE, which a bulk query delete
    # bypasses at the ORM level.
    session_ids = [
        session_id
        for (session_id,) in db.query(ChatSession.id)
        .filter(ChatSession.dataset_id == dataset.id)
        .all()
    ]

    if session_ids:
        db.query(ChatMessage).filter(
            ChatMessage.session_id.in_(session_ids)
        ).delete(synchronize_session=False)

        db.query(ChatSession).filter(
            ChatSession.id.in_(session_ids)
        ).delete(synchronize_session=False)

    # Cloud dataset
    if is_cloud_dataset(dataset.file_path):
        cleaned_storage_id = (
            _build_cleaned_storage_id(
                dataset.id
            )
            .removeprefix("supabase:")
        )

        # Delete original Supabase dataset
        delete_dataset_storage(
            dataset.file_path
        )

        # Delete cleaned Supabase dataset
        try:
            supabase_storage.delete_file(
                cleaned_storage_id
            )
        except Exception:
            logger.exception(
                "Failed to delete cleaned Supabase object "
                "for dataset_id=%s",
                dataset.id,
            )

        # Delete database record
        db.delete(dataset)
        db.commit()

        return

    # Local dataset
    try:
        original_path = resolve_dataset_path(
            dataset.file_path
        )
    except ValueError:
        original_path = None

    if original_path is not None:
        # Delete original file
        if original_path.exists():
            original_path.unlink()

        # Determine cleaned extension
        extension = (
            original_path.suffix.lower()
        )

        if extension == ".xls":
            cleaned_extension = ".xlsx"
        else:
            cleaned_extension = extension

        cleaned_path = (
            original_path.parent
            / f"{original_path.stem}"
            f"_cleaned"
            f"{cleaned_extension}"
        )

        # Delete cleaned file
        if cleaned_path.exists():
            cleaned_path.unlink()

    # Delete database record
    db.delete(dataset)
    db.commit()