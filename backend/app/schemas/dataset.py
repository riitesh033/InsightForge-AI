from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetBase(BaseModel):
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    rows: int
    columns: int


class DatasetCreate(DatasetBase):
    owner_id: int
    file_path: str


class DatasetResponse(DatasetBase):
    id: int
    owner_id: int
    file_path: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)