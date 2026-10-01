from pydantic import BaseModel, Field


class RejectStudentApplicationRequest(BaseModel):
    rejection_reason: str = Field(min_length=1, max_length=2000)
