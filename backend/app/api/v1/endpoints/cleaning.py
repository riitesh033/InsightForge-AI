from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.dataset import Dataset
from app.models.user import User
from app.services.cleaning import (
    apply_cleaning,
    get_cleaned_file_path,
    preview_cleaning,
)
from app.services.dataset_storage import (
    cleanup_dataset_local_path,
    get_dataset_local_path,
    is_cloud_dataset,
)
from app.services.entitlements import require_feature

router = APIRouter()


def get_user_dataset(
    dataset_id: int,
    db: Session,
    current_user: User,
) -> Dataset:
    dataset = (
        db.query(Dataset)
        .filter(
            Dataset.id == dataset_id,
            Dataset.owner_id == current_user.id,
        )
        .first()
    )

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    return dataset


def cleanup_temporary_file(
    file_path: str,
) -> None:
    """
    Remove a temporary downloaded cleaned dataset
    after the HTTP response has completed.
    """

    try:
        Path(file_path).unlink(
            missing_ok=True
        )
    except Exception:
        # Cleanup failure must never affect the completed
        # download response.
        pass


def ensure_dataset_source_exists(dataset: Dataset) -> None:
    """Return a safe not-found error before enforcing paid features."""

    try:
        path, temporary = get_dataset_local_path(dataset.file_path)
    except (FileNotFoundError, ValueError, RuntimeError):
        raise HTTPException(
            status_code=404,
            detail="Dataset file not found on server.",
        ) from None

    cleanup_dataset_local_path(path, temporary)


@router.post("/{dataset_id}/preview")
def preview_cleaning_route(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = get_user_dataset(
        dataset_id,
        db,
        current_user,
    )

    # Cloud-backed datasets are resolved by the preview service itself.
    # Avoid downloading the full remote dataset twice just to check existence.
    require_feature(
        db,
        current_user.id,
        "data_cleaning",
    )

    if not is_cloud_dataset(dataset.file_path):
        ensure_dataset_source_exists(dataset)

    return preview_cleaning(dataset)


@router.post("/{dataset_id}/apply")
def apply_cleaning_route(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = get_user_dataset(
        dataset_id,
        db,
        current_user,
    )

    # Cloud-backed datasets are resolved by the cleaning service itself.
    # Avoid a second full Supabase download before applying cleaning.
    require_feature(
        db,
        current_user.id,
        "data_cleaning",
    )

    if not is_cloud_dataset(dataset.file_path):
        ensure_dataset_source_exists(dataset)

    return apply_cleaning(dataset)


@router.get("/{dataset_id}/download")
def download_cleaned_dataset(
    dataset_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = get_user_dataset(
        dataset_id,
        db,
        current_user,
    )

    if is_cloud_dataset(dataset.file_path):
        ensure_dataset_source_exists(dataset)

    require_feature(
        db,
        current_user.id,
        "data_cleaning",
    )

    if not is_cloud_dataset(dataset.file_path):
        ensure_dataset_source_exists(dataset)

    cleaned_path = get_cleaned_file_path(
        dataset
    )

    # A Supabase-backed cleaned file is reconstructed
    # into a temporary local file. Delete it only after
    # FastAPI has finished sending the response.
    if is_cloud_dataset(
        dataset.file_path
    ):
        background_tasks.add_task(
            cleanup_temporary_file,
            str(cleaned_path),
        )

    return FileResponse(
        path=cleaned_path,
        filename=cleaned_path.name,
        media_type="application/octet-stream",
        background=background_tasks,
    )
