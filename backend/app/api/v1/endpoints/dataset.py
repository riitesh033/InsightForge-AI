import logging
import tempfile
from datetime import UTC, datetime, timedelta
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
from app.models.upload_session import UploadSession
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

UPLOAD_SESSION_EXPIRY_HOURS = 24


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


def _get_upload_session(
    db: Session,
    storage_id: str,
    current_user: User,
) -> UploadSession:
    """
    Return an upload session owned by the current user.

    Expired sessions cannot be used for further upload operations.
    """

    upload_session = (
        db.query(UploadSession)
        .filter(
            UploadSession.storage_id == storage_id,
            UploadSession.owner_id == current_user.id,
        )
        .first()
    )

    if upload_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload session not found.",
        )

    if upload_session.expires_at <= datetime.now(UTC).replace(
        tzinfo=None
    ):
        upload_session.status = "expired"
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Upload session has expired.",
        )

    return upload_session


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

    Creates a persistent upload session tied to the authenticated
    user before the browser starts uploading individual chunks.
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

    chunk_size = supabase_storage.chunk_size

    total_chunks = (
        payload.file_size + chunk_size - 1
    ) // chunk_size

    expires_at = (
        datetime.now(UTC).replace(tzinfo=None)
        + timedelta(hours=UPLOAD_SESSION_EXPIRY_HOURS)
    )

    upload_session = UploadSession(
        storage_id=storage_id,
        owner_id=current_user.id,
        filename=original_filename,
        file_size=payload.file_size,
        chunk_size=chunk_size,
        total_chunks=total_chunks,
        status="initialized",
        expires_at=expires_at,
    )

    try:
        db.add(upload_session)
        db.commit()
        db.refresh(upload_session)

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to create upload session."
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to initialize dataset upload.",
        ) from None

    return {
        "storage_id": storage_id,
        "original_filename": original_filename,
        "file_type": extension.replace(
            ".",
            "",
        ),
        "file_size": payload.file_size,
        "chunk_size": chunk_size,
        "total_chunks": total_chunks,
        "upload_session_id": upload_session.id,
        "expires_at": upload_session.expires_at.isoformat(),
    }


@router.post(
    "/upload/chunk-url",
)
def create_dataset_chunk_upload_url(
    storage_id: str,
    chunk_index: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a short-lived signed upload URL for one dataset chunk.

    The upload session is checked against the authenticated user so
    one user cannot request signed URLs for another user's upload.
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

    upload_session = _get_upload_session(
        db=db,
        storage_id=storage_id,
        current_user=current_user,
    )

    if chunk_index >= upload_session.total_chunks:
        raise HTTPException(
            status_code=400,
            detail="Chunk index is outside the upload session.",
        )

    if upload_session.status in {
        "completed",
        "cancelled",
    }:
        raise HTTPException(
            status_code=409,
            detail="Upload session is no longer active.",
        )

    if upload_session.status == "initialized":
        upload_session.status = "uploading"
        db.commit()

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

    The upload session is validated against the authenticated user
    before the chunks are reconstructed and analyzed.
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

    upload_session = _get_upload_session(
        db=db,
        storage_id=storage_id,
        current_user=current_user,
    )

    if upload_session.status == "completed":
        raise HTTPException(
            status_code=409,
            detail="Upload session has already been completed.",
        )

    if upload_session.status == "cancelled":
        raise HTTPException(
            status_code=409,
            detail="Upload session has been cancelled.",
        )

    if file_size != upload_session.file_size:
        raise HTTPException(
            status_code=400,
            detail="File size does not match the upload session.",
        )

    if total_chunks != upload_session.total_chunks:
        raise HTTPException(
            status_code=400,
            detail="Total chunks do not match the upload session.",
        )

    if safe_filename != upload_session.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename does not match the upload session.",
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

        upload_session.status = "completed"
        db.commit()

        if not settings.USE_CLOUD_STORAGE:
            supabase_storage.delete_file(storage_id)

        return dataset

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()

        upload_session.status = "failed"

        try:
            db.commit()
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
