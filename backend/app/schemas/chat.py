from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ============================================================
# Create Message
# ============================================================

class ChatMessageCreate(BaseModel):
    message: str
    session_id: int | None = None


# ============================================================
# Message Response
# ============================================================

class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# Chat Session Response
# ============================================================

class ChatSessionResponse(BaseModel):
    id: int
    dataset_id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# Chat Response
# ============================================================

class ChatResponse(BaseModel):
    session_id: int
    dataset_id: int
    answer: str
    messages: list[ChatMessageResponse]


# ============================================================
# Session Messages Response
# ============================================================

class ChatSessionMessagesResponse(BaseModel):
    session_id: int
    dataset_id: int
    messages: list[ChatMessageResponse]