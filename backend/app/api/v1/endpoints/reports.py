from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.models.user import User
from app.services.report import generate_analysis_report


router = APIRouter()


@router.get(
    "/{dataset_id}/download"
)
def download_report(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # =========================
    # Find Dataset
    # =========================

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
            status_code=404,
            detail="Dataset not found.",
        )

    # =========================
    # Find Analysis
    # =========================

    analysis = (
        db.query(Analysis)
        .filter(
            Analysis.dataset_id == dataset_id,
        )
        .first()
    )

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found.",
        )

    # =========================
    # Generate PDF
    # =========================

    pdf = generate_analysis_report(
        analysis
    )

    filename = (
        f"{dataset.original_filename}"
        .rsplit(".", 1)[0]
        + "_analysis_report.pdf"
    )

    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )