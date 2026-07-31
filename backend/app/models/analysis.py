from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import Text
from sqlalchemy import Integer
from sqlalchemy.orm import relationship

from app.db.base_models import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    dataset_id = Column(
        Integer,
        ForeignKey(
            "datasets.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    summary = Column(
        JSON,
        nullable=False,
    )

    column_info = Column(
        JSON,
        nullable=False,
    )

    statistics = Column(
        JSON,
        nullable=False,
    )

    missing_values = Column(
        JSON,
        nullable=False,
    )

    duplicates = Column(
        JSON,
        nullable=False,
    )

    correlations = Column(
        JSON,
        nullable=True,
    )

    outliers = Column(
        JSON,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    dataset = relationship(
        "Dataset",
        back_populates="analysis",
    )

    summary_text = Column(
    Text,
    nullable=False,
)

quality_score = Column(
    Integer,
    nullable=False,
    default=100,
)