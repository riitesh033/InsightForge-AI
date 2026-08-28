from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession


# ============================================================
# Get Single Session
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
# Get Sessions For Dataset
# ============================================================

def get_chat_sessions_for_dataset(
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
        .order_by(
            ChatSession.updated_at.desc()
        )
        .all()
    )


# ============================================================
# Create Session
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
# Delete Session
# ============================================================

def delete_chat_session(
    db: Session,
    session: ChatSession,
):
    db.delete(session)
    db.commit()


# ============================================================
# Create Message
# ============================================================

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

    # Update session timestamp so the chat
    # moves to the top of the sidebar.
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id
        )
        .first()
    )

    if session:
        from datetime import datetime

        session.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(message)

    return message


# ============================================================
# Get Messages
# ============================================================

def get_chat_messages(
    db: Session,
    session_id: int,
):
    return (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id
        )
        .order_by(
            ChatMessage.created_at.asc()
        )
        .all()
    )