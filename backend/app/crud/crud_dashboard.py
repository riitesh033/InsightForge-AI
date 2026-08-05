from sqlalchemy import extract
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


def get_uploads_per_month(
    db: Session,
    owner_id: int,
):
    uploads = (
        db.query(
            extract("month", Dataset.uploaded_at).label("month"),
            func.count(Dataset.id).label("uploads"),
        )
        .filter(Dataset.owner_id == owner_id)
        .group_by(extract("month", Dataset.uploaded_at))
        .order_by(extract("month", Dataset.uploaded_at))
        .all()
    )

    month_names = [
        "",
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    return [
        {
            "month": month_names[int(item.month)],
            "uploads": item.uploads,
        }
        for item in uploads
    ]


def get_file_type_distribution(
    db: Session,
    owner_id: int,
):
    result = (
        db.query(
            Dataset.file_type,
            func.count(Dataset.id).label("count"),
        )
        .filter(Dataset.owner_id == owner_id)
        .group_by(Dataset.file_type)
        .all()
    )

    return [
        {
            "file_type": item.file_type.upper(),
            "count": item.count,
        }
        for item in result
    ]


def get_quality_distribution(
    db: Session,
    owner_id: int,
):
    analyses = (
        db.query(Analysis)
        .join(Dataset)
        .filter(Dataset.owner_id == owner_id)
        .all()
    )

    distribution = {
        "90-100": 0,
        "80-89": 0,
        "70-79": 0,
        "60-69": 0,
        "<60": 0,
    }

    for analysis in analyses:
        score = analysis.quality_score

        if score >= 90:
            distribution["90-100"] += 1
        elif score >= 80:
            distribution["80-89"] += 1
        elif score >= 70:
            distribution["70-79"] += 1
        elif score >= 60:
            distribution["60-69"] += 1
        else:
            distribution["<60"] += 1

    return [
        {
            "range": key,
            "count": value,
        }
        for key, value in distribution.items()
    ]