from sqlalchemy.orm import Session

from app.crud.crud_dashboard import (
    get_dashboard_stats,
    get_file_type_distribution,
    get_quality_distribution,
    get_recent_analyses,
    get_recent_datasets,
    get_uploads_per_month,
)


def get_dashboard_data(
    db: Session,
    owner_id: int,
):
    return {
        "stats": get_dashboard_stats(
            db=db,
            owner_id=owner_id,
        ),
        "recent_datasets": get_recent_datasets(
            db=db,
            owner_id=owner_id,
        ),
        "recent_analyses": get_recent_analyses(
            db=db,
            owner_id=owner_id,
        ),
        "charts": {
            "uploads_per_month": get_uploads_per_month(
                db=db,
                owner_id=owner_id,
            ),
            "file_types": get_file_type_distribution(
                db=db,
                owner_id=owner_id,
            ),
            "quality_distribution": get_quality_distribution(
                db=db,
                owner_id=owner_id,
            ),
        },
    }