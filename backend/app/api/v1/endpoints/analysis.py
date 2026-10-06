import logging

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
    DatasetExplanationResponse,
    VerifiedAnalysisResponse,
)
from app.services.insight_engine import (
    generate_professional_insights,
)
from app.services.report import generate_analysis_report
from app.services.entitlements import require_feature
from app.services.verified_analysis import (
    build_verified_analysis_report,
)
from app.services.insights import generate_dataset_explanation


router = APIRouter()
logger = logging.getLogger(__name__)


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
    "/{dataset_id}/explanation",
    response_model=DatasetExplanationResponse,
)
async def get_dataset_explanation(
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

    cached_explanation = (
        analysis.summary.get("ai_explanation")
        if isinstance(analysis.summary, dict)
        else None
    )
    if isinstance(cached_explanation, str) and cached_explanation.strip():
        return DatasetExplanationResponse(
            available=True,
            explanation=cached_explanation,
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

    verified_analysis = build_verified_analysis_report(
        analysis=analysis,
        dataset=dataset,
    )
    insights = generate_professional_insights(
        report=verified_analysis,
    )
    facts = {
        "dataset": verified_analysis.dataset.model_dump(mode="json"),
        "data_quality": verified_analysis.data_quality.model_dump(mode="json"),
        "column_info": [
            item.model_dump(mode="json")
            for item in verified_analysis.column_info[:30]
        ],
        "statistics": [
            item.model_dump(mode="json")
            for item in verified_analysis.statistics[:12]
        ],
        "correlations": [
            item.model_dump(mode="json")
            for item in sorted(
                verified_analysis.correlations,
                key=lambda item: abs(item.coefficient),
                reverse=True,
            )[:8]
        ],
        "potential_outliers": [
            item.model_dump(mode="json")
            for item in verified_analysis.outliers
            if item.count > 0
        ][:8],
        "recommendations": [
            {
                "finding": item.finding,
                "recommended_action": item.recommended_action,
            }
            for item in insights.top_actions
        ],
    }
    explanation = await generate_dataset_explanation(facts)
    if explanation is None:
        return DatasetExplanationResponse(
            available=False,
            explanation=(
                "AI explanation is temporarily unavailable. "
                "Your deterministic dataset analysis is still available."
            ),
        )

    analysis.summary = {
        **(analysis.summary if isinstance(analysis.summary, dict) else {}),
        "ai_explanation": explanation,
    }
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to cache the dataset AI explanation")
        return DatasetExplanationResponse(
            available=False,
            explanation=(
                "AI explanation is temporarily unavailable. "
                "Your deterministic dataset analysis is still available."
            ),
        )
    return DatasetExplanationResponse(
        available=True,
        explanation=explanation,
    )


@router.get(
    "/{dataset_id}/report",
)
def generate_dataset_report(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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

    require_feature(db, current_user.id, "professional_reports")

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

    try:
        pdf = generate_analysis_report(
            dataset,
            analysis,
        )
    except FileNotFoundError:
        logger.warning("Analysis report source file is unavailable")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report source file is unavailable.",
        ) from None
    except ValueError:
        logger.exception("Analysis report data is invalid")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to generate report from this dataset.",
        ) from None
    except Exception:
        logger.exception("Unexpected analysis report generation failure")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate analysis report.",
        ) from None

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