from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportResponse(BaseModel):
    id: int
    analysis_id: int
    dataset_id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )