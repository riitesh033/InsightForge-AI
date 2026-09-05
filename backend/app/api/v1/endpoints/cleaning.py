from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.crud.crud_dataset import get_dataset
from app.db.session import get_db
from app.models.user import User
from app.schemas.cleaning import CleaningResponse
from app.services.cleaning import (
    apply_cleaning,
    get_cleaned_file_path,
    preview_cleaning,
)


router = APIRouter()


@router.post(
    "/{dataset_id}/preview",
    response_model=CleaningResponse,
)
def preview_cleaning_route(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = get_dataset(
        db=db,
        dataset_id=dataset_id,
        owner_id=current_user.id,
    )

    if dataset is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    result = preview_cleaning(dataset)

    return {
        **result,
        "cleaned_filename": None,
        "download_available": False,
    }


@router.post(
    "/{dataset_id}/apply",
    response_model=CleaningResponse,
)
def apply_cleaning_route(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = get_dataset(
        db=db,
        dataset_id=dataset_id,
        owner_id=current_user.id,
    )

    if dataset is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    result = apply_cleaning(dataset)

    return result


@router.get(
    "/{dataset_id}/download",
)
def download_cleaned_dataset_route(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = get_dataset(
        db=db,
        dataset_id=dataset_id,
        owner_id=current_user.id,
    )

    if dataset is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    cleaned_path = get_cleaned_file_path(dataset)

    return FileResponse(
        path=cleaned_path,
        filename=cleaned_path.name,
        media_type="application/octet-stream",
    )