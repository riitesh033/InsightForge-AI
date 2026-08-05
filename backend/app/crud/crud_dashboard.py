from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.models.analysis import Analysis
from app.models.dataset import Dataset


def get_dashboard_stats(
    db: Session,
    owner_id: int,
):
    total_datasets = (
        db.query(func.count(Dataset.id))
        .filter(Dataset.owner_id == owner_id)
        .scalar()
        or 0
    )

    total_rows = (
        db.query(func.coalesce(func.sum(Dataset.rows), 0))
        .filter(Dataset.owner_id == owner_id)
        .scalar()
        or 0
    )

    total_analyses = (
        db.query(func.count(Analysis.id))
        .join(Dataset)
        .filter(Dataset.owner_id == owner_id)
        .scalar()
        or 0
    )

    average_quality = (
        db.query(func.avg(Analysis.quality_score))
        .join(Dataset)
        .filter(Dataset.owner_id == owner_id)
        .scalar()
        or 0
    )

    return {
        "total_datasets": total_datasets,
        "total_analyses": total_analyses,
        "average_quality_score": round(float(average_quality), 2),
        "total_rows": total_rows,
    }


def get_recent_datasets(
    db: Session,
    owner_id: int,
    limit: int = 5,
):
    datasets = (
        db.query(Dataset)
        .options(joinedload(Dataset.analysis))
        .filter(Dataset.owner_id == owner_id)
        .order_by(Dataset.uploaded_at.desc())
        .limit(limit)
        .all()
    )

    result = []

    for dataset in datasets:
        result.append(
            {
                "id": dataset.id,
                "filename": dataset.filename,
                "original_filename": dataset.original_filename,
                "rows": dataset.rows,
                "columns": dataset.columns,
                "uploaded_at": dataset.uploaded_at,
                "quality_score": (
                    dataset.analysis.quality_score
                    if dataset.analysis
                    else None
                ),
            }
        )

    return result


def get_recent_analyses(
    db: Session,
    owner_id: int,
    limit: int = 5,
):
    analyses = (
        db.query(Analysis)
        .join(Dataset)
        .filter(Dataset.owner_id == owner_id)
        .order_by(Analysis.created_at.desc())
        .limit(limit)
        .all()
    )

    result = []

    for analysis in analyses:
        result.append(
            {
                "analysis_id": analysis.id,
                "dataset_id": analysis.dataset.id,
                "dataset_name": analysis.dataset.original_filename,
                "quality_score": analysis.quality_score,
                "created_at": analysis.created_at,
            }
        )

    return result