import logging
from pathlib import Path
from uuid import uuid4

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
from app.core.config import settings
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
    DatasetUploadInit,
)
from app.services.cloud_storage import supabase_storage
from app.services.dataset import upload_dataset
from app.services.dataset_storage import (
    cleanup_dataset_local_path,
    get_dataset_local_path,
)
from app.services.entitlements import (
    enforce_dataset_count,
    enforce_upload_size,
    lock_user_for_quota,
)


logger = logging.getLogger(__name__)

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
    "/upload/init",
)
def initialize_dataset_upload(
    payload: DatasetUploadInit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Initialize a direct browser-to-Supabase dataset upload.

    The browser receives a storage ID that is used for the
    individual dataset chunks.
    """

    if not payload.filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )

    original_filename = Path(
        payload.filename.replace("\\", "/")
    ).name

    extension = Path(
        original_filename
    ).suffix.lower()

    allowed_extensions = {
        ".csv",
        ".xlsx",
        ".xls",
    }

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only CSV, XLSX and XLS files are supported."
            ),
        )

    if payload.file_size <= 0:
        raise HTTPException(
            status_code=400,
            detail="File size must be greater than zero.",
        )

    # Preserve the existing quota checks.
    lock_user_for_quota(
        db,
        current_user.id,
    )

    enforce_dataset_count(
        db,
        current_user.id,
    )

    enforce_upload_size(
        db,
        current_user.id,
        payload.file_size,
    )

    if not supabase_storage.is_configured():
        raise HTTPException(
            status_code=500,
            detail=(
                "Chunked upload storage is unavailable because "
                "Supabase Storage is not configured."
            ),
        )

    storage_id = (
        f"datasets/uploads/"
        f"{uuid4().hex}"
    )

    return {
        "storage_id": storage_id,
        "original_filename": original_filename,
        "file_type": extension.replace(
            ".",
            "",
        ),
        "file_size": payload.file_size,
        "chunk_size": supabase_storage.chunk_size,
    }

@router.post(
    "/upload/finalize",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
)
def finalize_dataset_upload(
    storage_id: str,
    original_filename: str,
    file_size: int,
    total_chunks: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Finalize a direct browser-to-Supabase dataset upload.

    The uploaded chunks are reconstructed into a temporary local
    file and passed through the existing dataset analysis workflow.
    """

    if not storage_id.startswith("datasets/uploads/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid dataset storage ID.",
        )

    if file_size <= 0:
        raise HTTPException(
            status_code=400,
            detail="File size must be greater than zero.",
        )

    if total_chunks <= 0:
        raise HTTPException(
            status_code=400,
            detail="Total chunks must be greater than zero.",
        )

    safe_filename = Path(
        original_filename.replace("\\", "/")
    ).name

    extension = Path(
        safe_filename
    ).suffix.lower()

    if extension not in {
        ".csv",
        ".xlsx",
        ".xls",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only CSV, XLSX and XLS files are supported."
            ),
        )

    if not supabase_storage.is_configured():
        raise HTTPException(
            status_code=500,
            detail=(
                "Chunked upload storage is unavailable because "
                "Supabase Storage is not configured."
            ),
        )

    # Re-check quota before creating the permanent dataset record.
    lock_user_for_quota(
        db,
        current_user.id,
    )

    enforce_dataset_count(
        db,
        current_user.id,
    )

    enforce_upload_size(
        db,
        current_user.id,
        file_size,
    )

    temporary_path: Path | None = None

    try:
        # Create the manifest for the browser-uploaded chunks.
        supabase_storage.create_chunk_manifest(
            storage_id=storage_id,
            total_chunks=total_chunks,
            file_size=file_size,
        )

        import tempfile

        temporary_directory = Path(
            tempfile.mkdtemp(
                prefix="insightforge-upload-"
            )
        )

        temporary_path = (
            temporary_directory
            / safe_filename
        )

        # Reconstruct the Supabase chunks locally.
        supabase_storage.download_chunks_to_file(
            storage_id=storage_id,
            output_path=temporary_path,
            total_chunks=total_chunks,
        )

        if not temporary_path.is_file():
            raise FileNotFoundError(
                "Reconstructed dataset file was not created."
            )

        reconstructed_size = (
            temporary_path.stat().st_size
        )

        if reconstructed_size != file_size:
            raise ValueError(
                "Reconstructed dataset size does not "
                "match the uploaded file size."
            )

        # ``upload_dataset`` expects an UploadFile. Wrapping the
        # reconstructed temporary file lets the chunked upload reuse the
        # exact profiling/analysis workflow used by a direct upload.
        #
        # The storage identifier is passed through so the resulting record
        # points at the Supabase copy that the browser already uploaded;
        # ``upload_dataset`` derives the stored location itself and the
        # temporary reconstruction is removed in the ``finally`` block.
        from fastapi import UploadFile as FastAPIUploadFile

        with temporary_path.open("rb") as dataset_file:
            upload_file = FastAPIUploadFile(
                file=dataset_file,
                filename=safe_filename,
            )

            dataset = upload_dataset(
                db=db,
                file=upload_file,
                owner_id=current_user.id,
                existing_cloud_storage_id=(
                    f"supabase:{storage_id}"
                    if settings.USE_CLOUD_STORAGE
                    else None
                ),
            )

        if not settings.USE_CLOUD_STORAGE:
            supabase_storage.delete_file(storage_id)

        return dataset

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to finalize dataset upload."
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to finalize dataset upload.",
        ) from None

    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(
                    missing_ok=True
                )

                temporary_path.parent.rmdir()

            except OSError:
                pass

@router.post(
    "/upload/chunk-url",
)
def create_dataset_chunk_upload_url(
    storage_id: str,
    chunk_index: int,
    current_user: User = Depends(get_current_user),
):
    """
    Create a short-lived signed upload URL for one dataset chunk.

    The browser uploads the chunk directly to Supabase, so the
    large dataset does not have to pass through the Render server.
    """

    if not storage_id:
        raise HTTPException(
            status_code=400,
            detail="Storage ID is required.",
        )

    if not storage_id.startswith("datasets/uploads/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid dataset storage ID.",
        )

    if chunk_index < 0:
        raise HTTPException(
            status_code=400,
            detail="Chunk index must be non-negative.",
        )

    if not supabase_storage.is_configured():
        raise HTTPException(
            status_code=500,
            detail=(
                "Chunked upload storage is unavailable because "
                "Supabase Storage is not configured."
            ),
        )

    try:
        signed_upload = (
            supabase_storage.create_signed_chunk_upload_url(
                storage_id=storage_id,
                chunk_index=chunk_index,
            )
        )

    except Exception:
        logger.exception(
            "Failed to create Supabase signed chunk upload URL."
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to initialize dataset chunk upload.",
        ) from None

    return {
        "storage_id": storage_id,
        "chunk_index": chunk_index,
        "path": signed_upload["path"],
        "token": signed_upload["token"],
    }


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
