from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.crud.crud_dataset import (
    delete_dataset,
    get_dataset,
    get_datasets,
    rename_dataset,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.dataset import (
    DatasetListResponse,
    DatasetRename,
    DatasetResponse,
)
from app.services.dataset import upload_dataset

router = APIRouter()


@router.post(
    "/upload",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
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
    response_model=DatasetListResponse,
)
def get_all_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    sort_by: str = Query("uploaded_at"),
    order: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_datasets(
        db=db,
        owner_id=current_user.id,
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        order=order,
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
    status_code=status.HTTP_204_NO_CONTENT,
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

    file_path = Path(dataset.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server.",
        )

    return FileResponse(
        path=file_path,
        filename=dataset.original_filename,
        media_type="application/octet-stream",
    )