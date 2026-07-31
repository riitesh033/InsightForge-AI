from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AnalysisBase(BaseModel):
    summary: dict
    summary_text: str
    column_info: list
    statistics: dict
    missing_values: dict
    duplicates: dict
    correlations: dict | None = None
    outliers: dict | None = None


class AnalysisCreate(AnalysisBase):
    dataset_id: int


class AnalysisResponse(AnalysisBase):
    id: int
    dataset_id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )