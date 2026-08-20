from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatMessageCreate(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ChatResponse(BaseModel):
    session_id: int
    dataset_id: int
    answer: str
    messages: list[ChatMessageResponse]