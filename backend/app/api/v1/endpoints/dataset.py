from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
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
from app.services.dataset_storage import (
    cleanup_dataset_local_path,
    get_dataset_local_path,
)


router = APIRouter()


def cleanup_downloaded_dataset(
    file_path: str,
    temporary: bool,
) -> None:
    """
    Remove a temporary reconstructed dataset after
    the download response has completed.
    """

    if not temporary:
        return

    try:
        cleanup_dataset_local_path(
            Path(file_path),
            True,
        )
    except Exception:
        # Cleanup failure must never affect the download.
        pass


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
    page_size: int = Query(
        10,
        ge=1,
        le=100,
    ),
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


# IMPORTANT:
# Keep download BEFORE /{dataset_id}
@router.get(
    "/{dataset_id}/download"
)
def download_dataset_route(
    dataset_id: int,
    background_tasks: BackgroundTasks,
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
            status_code=404,
            detail="Dataset not found.",
        )

    try:
        file_path, temporary = (
            get_dataset_local_path(
                dataset.file_path
            )
        )

    except (
        FileNotFoundError,
        ValueError,
        RuntimeError,
    ):
        raise HTTPException(
            status_code=404,
            detail="File not found on server.",
        ) from None

    if not file_path.is_file():
        cleanup_dataset_local_path(
            file_path,
            temporary,
        )

        raise HTTPException(
            status_code=404,
            detail="File not found on server.",
        )

    # Supabase datasets are reconstructed into a temporary
    # Render/local file. Delete that file only after FastAPI
    # finishes sending the response.
    if temporary:
        background_tasks.add_task(
            cleanup_downloaded_dataset,
            str(file_path),
            temporary,
        )

    return FileResponse(
        path=file_path,
        filename=dataset.original_filename,
        media_type="application/octet-stream",
        background=background_tasks,
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
            status_code=404,
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
            status_code=404,
            detail="Dataset not found.",
        )

    delete_dataset(
        db=db,
        dataset=dataset,
    )