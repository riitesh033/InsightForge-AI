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
from app.services.dataset_storage import is_cloud_dataset
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

    require_feature(
        db,
        current_user.id,
        "data_cleaning",
    )

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

    require_feature(
        db,
        current_user.id,
        "data_cleaning",
    )

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

    require_feature(
        db,
        current_user.id,
        "data_cleaning",
    )

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