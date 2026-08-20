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
    get_chat_messages,
    get_chat_session_for_dataset,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatResponse,
)
from app.services.chat import (
    generate_chat_answer,
    get_dataset_context,
)


router = APIRouter()


@router.post(
    "/{dataset_id}",
    response_model=ChatResponse,
)
def chat_with_dataset(
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

    session = get_chat_session_for_dataset(
        db=db,
        dataset_id=dataset_id,
        user_id=current_user.id,
    )

    if session is None:
        session = create_chat_session(
            db=db,
            dataset_id=dataset_id,
            user_id=current_user.id,
        )

    create_chat_message(
        db=db,
        session_id=session.id,
        role="user",
        content=question,
    )

    answer = generate_chat_answer(
        question=question,
        context=context,
    )

    create_chat_message(
        db=db,
        session_id=session.id,
        role="assistant",
        content=answer,
    )

    messages = get_chat_messages(
        db=db,
        session_id=session.id,
    )

    return ChatResponse(
        session_id=session.id,
        dataset_id=dataset_id,
        answer=answer,
        messages=[
            ChatMessageResponse.model_validate(
                message
            )
            for message in messages
        ],
    )