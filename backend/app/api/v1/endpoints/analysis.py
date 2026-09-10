from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.crud.crud_analysis import get_analysis
from app.db.session import get_db
from app.models.dataset import Dataset
from app.models.user import User
from app.schemas.verified_analysis_response import (
    VerifiedAnalysisResponse,
)
from app.services.insight_engine import (
    generate_professional_insights,
)
from app.services.report import generate_analysis_report
from app.services.verified_analysis import (
    build_verified_analysis_report,
)


router = APIRouter()


@router.get(
    "/{dataset_id}",
    response_model=VerifiedAnalysisResponse,
)
def get_dataset_analysis(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analysis = get_analysis(
        db=db,
        dataset_id=dataset_id,
        owner_id=current_user.id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found.",
        )

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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    verified_analysis = (
        build_verified_analysis_report(
            analysis=analysis,
            dataset=dataset,
        )
    )

    insights = generate_professional_insights(
        report=verified_analysis,
    )

    return VerifiedAnalysisResponse(
        analysis_id=analysis.id,
        created_at=analysis.created_at.isoformat(),
        verified_analysis=verified_analysis,
        insights=insights,
    )


@router.get(
    "/{dataset_id}/report",
)
def generate_dataset_report(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analysis = get_analysis(
        db=db,
        dataset_id=dataset_id,
        owner_id=current_user.id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found.",
        )

    pdf = generate_analysis_report(
        analysis
    )

    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; '
                f'filename="insightforge-analysis-{dataset_id}.pdf"'
            )
        },
    )