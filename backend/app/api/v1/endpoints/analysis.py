from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.crud.crud_analysis import (
    get_analysis,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.analysis import AnalysisResponse

router = APIRouter()


@router.get(
    "/{dataset_id}",
    response_model=AnalysisResponse,
)
def get_dataset_analysis(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    analysis = get_analysis(
        db=db,
        dataset_id=dataset_id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found.",
        )

    return analysis