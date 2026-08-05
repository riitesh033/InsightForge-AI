from datetime import datetime

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)


class RecentAnalysis(BaseModel):
    analysis_id: int
    dataset_id: int
    dataset_name: str
    quality_score: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UploadTrend(BaseModel):
    month: str
    uploads: int


class FileTypeDistribution(BaseModel):
    file_type: str
    count: int


class QualityDistribution(BaseModel):
    range: str
    count: int


class DashboardCharts(BaseModel):
    uploads_per_month: list[UploadTrend]
    file_types: list[FileTypeDistribution]
    quality_distribution: list[QualityDistribution]


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_datasets: list[RecentDataset]
    recent_analyses: list[RecentAnalysis]
    charts: DashboardCharts