from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user

from app.crud.crud_chat import (
    create_chat_message,
    create_chat_session,
    delete_chat_session,
    get_chat_messages,
    get_chat_session,
    get_chat_sessions_for_dataset,
)

from app.db.session import get_db

from app.models.user import User

from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatResponse,
    ChatSessionMessagesResponse,
    ChatSessionResponse,
)

from app.services.chat import (
    generate_chat_answer,
    get_dataset_context,
    is_legacy_safety_message,
)
from app.services.entitlements import (
    enforce_ai_query_limit,
    lock_user_for_quota,
    require_feature,
)
from app.models.chat_message import ChatMessage


router = APIRouter()


# ============================================================
# Get All Chat Sessions
# ============================================================

@router.get(
    "/{dataset_id}/sessions",
    response_model=list[ChatSessionResponse],
)
def get_sessions(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    context = get_dataset_context(
        db=db,
        dataset_id=dataset_id,
        user_id=current_user.id,
    )

    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    sessions = get_chat_sessions_for_dataset(
        db=db,
        dataset_id=dataset_id,
        user_id=current_user.id,
    )
    summaries = []
    for session, last_message in sessions:
        preview = last_message
        if preview and len(preview) > 180:
            preview = f"{preview[:177].rstrip()}..."
        summaries.append(
            ChatSessionResponse.model_validate(session).model_copy(
                update={"last_message": preview}
            )
        )
    return summaries


# ============================================================
# Create New Chat Session
# ============================================================

@router.post(
    "/{dataset_id}/sessions",
    response_model=ChatSessionResponse,
)
def create_session(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    context = get_dataset_context(
        db=db,
        dataset_id=dataset_id,
        user_id=current_user.id,
    )

    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    return create_chat_session(
        db=db,
        dataset_id=dataset_id,
        user_id=current_user.id,
        title="New Chat",
    )


# ============================================================
# Get Chat Messages
# ============================================================

@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionMessagesResponse,
)
def get_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = get_chat_session(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    messages = [
        message
        for message in get_chat_messages(
            db=db,
            session_id=session.id,
        )
        if not is_legacy_safety_message(
            message.role,
            message.content,
        )
    ]

    return ChatSessionMessagesResponse(
        session_id=session.id,
        dataset_id=session.dataset_id,
        messages=[
            ChatMessageResponse.model_validate(message)
            for message in messages
        ],
    )


# ============================================================
# Delete Chat Session
# ============================================================

@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = get_chat_session(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    delete_chat_session(
        db=db,
        session=session,
    )

    return None


# ============================================================
# Chat With Dataset
# ============================================================

@router.post(
    "/{dataset_id}",
    response_model=ChatResponse,
)
async def chat_with_dataset(
    dataset_id: int,
    request: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = request.message.strip()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty.",
        )

    # --------------------------------------------------------
    # Get Dataset
    # --------------------------------------------------------

    context = get_dataset_context(
        db=db,
        dataset_id=dataset_id,
        user_id=current_user.id,
    )

    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    require_feature(db, current_user.id, "ai_chat")

    # --------------------------------------------------------
    # Get Requested Session
    # --------------------------------------------------------

    session = None

    if request.session_id is not None:

        session = get_chat_session(
            db=db,
            session_id=request.session_id,
            user_id=current_user.id,
        )

        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found.",
            )

        if session.dataset_id != dataset_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chat session does not belong to this dataset.",
            )

    # --------------------------------------------------------
    # Create Session If Needed
    # --------------------------------------------------------

    if session is None:

        session = create_chat_session(
            db=db,
            dataset_id=dataset_id,
            user_id=current_user.id,
            title=question[:50],
        )

    lock_user_for_quota(db, current_user.id)
    enforce_ai_query_limit(db, current_user.id)

    if (
        session.title in {"New Chat", "Dataset Chat"}
        and db.query(ChatMessage.id)
        .filter(ChatMessage.session_id == session.id)
        .first()
        is None
    ):
        session.title = question[:50]

    # --------------------------------------------------------
    # Capture clean conversation history before adding the new turn.
    # --------------------------------------------------------

    previous_messages = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in get_chat_messages(
            db=db,
            session_id=session.id,
        )
        if not is_legacy_safety_message(
            message.role,
            message.content,
        )
    ]

    # --------------------------------------------------------
    # Save User Message
    # --------------------------------------------------------

    create_chat_message(
        db=db,
        session_id=session.id,
        role="user",
        content=question,
    )

    # --------------------------------------------------------
    # Generate AI Answer
    # --------------------------------------------------------

    answer = await generate_chat_answer(
        question=question,
        context=context,
        conversation_history=previous_messages,
    )

    # --------------------------------------------------------
    # Save Assistant Message
    # --------------------------------------------------------

    create_chat_message(
        db=db,
        session_id=session.id,
        role="assistant",
        content=answer,
    )

    # --------------------------------------------------------
    # Get Complete Conversation
    # --------------------------------------------------------

    messages = [
        message
        for message in get_chat_messages(
            db=db,
            session_id=session.id,
        )
        if not is_legacy_safety_message(
            message.role,
            message.content,
        )
    ]

    return ChatResponse(
        session_id=session.id,
        dataset_id=dataset_id,
        answer=answer,
        messages=[
            ChatMessageResponse.model_validate(message)
            for message in messages
        ],
    )