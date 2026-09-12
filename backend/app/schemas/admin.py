from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SystemHealthSchema(BaseModel):
    backend_status: str
    database_status: str
    ai_service_status: str
    storage_usage_mb: float

class AdminDashboardStats(BaseModel):
    total_users: int
    active_users: int
    total_datasets: int
    total_analyses: int
    total_reports: int
    total_chat_messages: int
    avg_quality_score: float

class AdminUserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    created_at: datetime
    dataset_count: int

    class Config:
        from_attributes = True

class AdminDatasetResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    row_count: Optional[int]
    column_count: Optional[int]
    file_size_bytes: int
    quality_score: Optional[float]
    created_at: datetime
    owner_email: str

    class Config:
        from_attributes = True