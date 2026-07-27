from sqlalchemy.orm import Session

from app.models.analysis import Analysis


def get_analysis(
    db: Session,
    dataset_id: int,
):
    return (
        db.query(Analysis)
        .filter(
            Analysis.dataset_id == dataset_id
        )
        .first()
    )


def create_analysis(
    db: Session,
    analysis: Analysis,
):
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return analysis


def delete_analysis(
    db: Session,
    dataset_id: int,
):
    analysis = get_analysis(
        db,
        dataset_id,
    )

    if analysis:
        db.delete(analysis)
        db.commit()

    return analysis