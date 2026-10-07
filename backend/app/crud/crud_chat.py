from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
import re


def _is_legacy_safety_message(content: str) -> bool:
    return bool(
        re.fullmatch(
            r"user\s+safety\s*:\s*safe\.?\s*",
            (content or "").strip(),
            re.IGNORECASE,
        )
    )


# ============================================================
# Get Single Chat Session
# ============================================================

def get_chat_session(
    db: Session,
    session_id: int,
    user_id: int,
):
    return (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        .first()
    )


# ============================================================
# Get All Chat Sessions For Dataset
# ============================================================

def get_chat_sessions_for_dataset(
    db: Session,
    dataset_id: int,
    user_id: int,
):
    last_message = (
        db.query(ChatMessage.content)
        .filter(
            ChatMessage.session_id == ChatSession.id,
            ~ChatMessage.content.op("~*")(r"^user\s+safety\s*:\s*safe\.?\s*$"),
        )
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(1)
        .correlate(ChatSession)
        .scalar_subquery()
    )
    return (
        db.query(ChatSession, last_message.label("last_message"))
        .filter(
            ChatSession.dataset_id == dataset_id,
            ChatSession.user_id == user_id,
        )
        .order_by(ChatSession.updated_at.desc())
        .all()
    )


# ============================================================
# Create Chat Session
# ============================================================

def create_chat_session(
    db: Session,
    dataset_id: int,
    user_id: int,
    title: str = "New Chat",
):
    session = ChatSession(
        dataset_id=dataset_id,
        user_id=user_id,
        title=title,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


# ============================================================
# Delete Chat Session
# ============================================================

def delete_chat_session(
    db: Session,
    session: ChatSession,
):
    db.delete(session)
    db.commit()


# ============================================================
# Create Chat Message
# ============================================================

def create_chat_message(
    db: Session,
    session_id: int,
    role: str,
    content: str,
):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id)
        .first()
    )
    if session is not None:
        session.updated_at = datetime.now(UTC).replace(tzinfo=None)

    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


# ============================================================
# Get Chat Messages
# ============================================================

def get_chat_messages(
    db: Session,
    session_id: int,
):
    return [
        message
        for message in (
            db.query(ChatMessage)
            .filter(
                ChatMessage.session_id == session_id,
            )
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        if not (
            message.role == "assistant"
            and _is_legacy_safety_message(message.content)
        )
    ]