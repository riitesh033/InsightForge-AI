from fastapi import APIRouter, Depends, HTTPException
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

    return apply_cleaning(dataset)


@router.get("/{dataset_id}/download")
def download_cleaned_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = get_user_dataset(
        dataset_id,
        db,
        current_user,
    )

    cleaned_path = get_cleaned_file_path(dataset)

    return FileResponse(
        path=cleaned_path,
        filename=cleaned_path.name,
        media_type="application/octet-stream",
    )