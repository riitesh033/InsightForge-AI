from sqlalchemy.orm import Session

from app.models.analysis import Analysis


def create_analysis(
    db: Session,
    analysis: Analysis,
):
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return analysis


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


def delete_analysis(
    db: Session,
    dataset_id: int,
):
    analysis = get_analysis(
        db=db,
        dataset_id=dataset_id,
    )

    if analysis is None:
        return None

    db.delete(analysis)
    db.commit()

    return analysis