from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.crud.crud_dataset import (
    delete_dataset,
    get_dataset,
    get_datasets,
    rename_dataset,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.dataset import DatasetRename, DatasetResponse
from app.services.dataset import upload_dataset

router = APIRouter()


@router.post(
    "/upload",
    response_model=DatasetResponse,
)
def upload_dataset_route(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return upload_dataset(
        db=db,
        file=file,
        owner_id=current_user.id,
    )


@router.get(
    "",
    response_model=list[DatasetResponse],
)
def get_all_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_datasets(
        db=db,
        owner_id=current_user.id,
    )


@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
)
def get_dataset_by_id(
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    return dataset


@router.patch(
    "/{dataset_id}",
    response_model=DatasetResponse,
)
def rename_dataset_route(
    dataset_id: int,
    payload: DatasetRename,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = get_dataset(
        db=db,
        dataset_id=dataset_id,
        owner_id=current_user.id,
    )

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    return rename_dataset(
        db=db,
        dataset=dataset,
        new_name=payload.original_filename,
    )


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_200_OK,
)
def delete_dataset_route(
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    delete_dataset(
        db=db,
        dataset=dataset,
    )

    return {
        "message": "Dataset deleted successfully."
    }


@router.get("/{dataset_id}/download")
def download_dataset_route(
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    return FileResponse(
        path=dataset.file_path,
        filename=dataset.original_filename,
        media_type="application/octet-stream",
    )