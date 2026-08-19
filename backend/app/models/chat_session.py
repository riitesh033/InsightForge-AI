from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import relationship

from app.db.base_models import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

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
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    title = Column(
        String(255),
        nullable=False,
        default="Dataset Chat",
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    dataset = relationship(
        "Dataset",
    )

    user = relationship(
        "User",
    )

    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )