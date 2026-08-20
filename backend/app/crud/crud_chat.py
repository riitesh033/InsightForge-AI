from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession


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


def get_chat_session_for_dataset(
    db: Session,
    dataset_id: int,
    user_id: int,
):
    return (
        db.query(ChatSession)
        .filter(
            ChatSession.dataset_id == dataset_id,
            ChatSession.user_id == user_id,
        )
        .order_by(ChatSession.updated_at.desc())
        .first()
    )


def create_chat_session(
    db: Session,
    dataset_id: int,
    user_id: int,
):
    session = ChatSession(
        dataset_id=dataset_id,
        user_id=user_id,
        title="Dataset Chat",
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


def create_chat_message(
    db: Session,
    session_id: int,
    role: str,
    content: str,
):
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


def get_chat_messages(
    db: Session,
    session_id: int,
):
    return (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id
        )
        .order_by(ChatMessage.created_at.asc())
        .all()
    )