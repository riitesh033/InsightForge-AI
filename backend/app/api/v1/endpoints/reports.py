from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.dataset import Dataset
from app.models.analysis import Analysis
from app.services.report import generate_analysis_report

router = APIRouter()


# ============================================================
# GET ALL REPORTS
# ============================================================

@router.get("/")
def get_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reports = (
        db.query(
            Dataset.id.label("dataset_id"),
            Dataset.original_filename.label("dataset_name"),
            Dataset.uploaded_at.label("uploaded_at"),
            Analysis.id.label("analysis_id"),
            Analysis.quality_score.label("quality_score"),
        )
        .join(
            Analysis,
            Analysis.dataset_id == Dataset.id,
        )
        .filter(
            Dataset.owner_id == current_user.id,
        )
        .order_by(
            Dataset.uploaded_at.desc()
        )
        .all()
    )

    return [
        {
            "dataset_id": report.dataset_id,
            "dataset_name": report.dataset_name,
            "uploaded_at": report.uploaded_at,
            "analysis_id": report.analysis_id,
            "quality_score": report.quality_score,
        }
        for report in reports
    ]


# ============================================================
# DOWNLOAD PDF REPORT
# ============================================================

@router.get("/{dataset_id}/pdf")
def download_report(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # --------------------------------------------------------
    # Find dataset belonging to current user
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Find analysis for dataset
    # --------------------------------------------------------

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
            detail="Analysis not found for this dataset.",
        )

    # --------------------------------------------------------
    # Generate professional PDF report
    #
    # IMPORTANT:
    # The report generator requires BOTH:
    #   dataset
    #   analysis
    # --------------------------------------------------------

    try:
        pdf_buffer = generate_analysis_report(
            dataset=dataset,
            analysis=analysis,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to generate analysis report: {str(exc)}",
        )

    # --------------------------------------------------------
    # Build download filename
    # --------------------------------------------------------

    original_name = dataset.original_filename or "dataset"

    if "." in original_name:
        report_name = original_name.rsplit(".", 1)[0]
    else:
        report_name = original_name

    filename = f"{report_name}_analysis_report.pdf"

    # --------------------------------------------------------
    # Return PDF
    # --------------------------------------------------------

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )