from sqlalchemy.orm import Session

from app.crud.crud_dashboard import (
    get_dashboard_stats,
    get_recent_analyses,
    get_recent_datasets,
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
    }