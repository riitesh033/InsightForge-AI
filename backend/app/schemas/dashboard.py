from datetime import datetime

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_datasets: int
    total_analyses: int
    average_quality_score: float
    total_rows: int


class RecentDataset(BaseModel):
    id: int
    filename: str
    original_filename: str
    rows: int
    columns: int
    uploaded_at: datetime
    quality_score: int | None = None

    model_config = {
        "from_attributes": True,
    }


class RecentAnalysis(BaseModel):
    analysis_id: int
    dataset_id: int
    dataset_name: str
    quality_score: int
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_datasets: list[RecentDataset]
    recent_analyses: list[RecentAnalysis]