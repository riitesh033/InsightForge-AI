from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.crud.crud_dataset import (
    get_dataset,
    get_datasets,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.dataset import DatasetResponse
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
    datasets = get_datasets(db)

    return datasets


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
    )

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    return dataset