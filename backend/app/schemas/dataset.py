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


class DatasetRename(BaseModel):
    original_filename: str


class DatasetListResponse(BaseModel):
    items: list[DatasetResponse]
    total: int
    page: int
    page_size: int
    pages: int


class DatasetQueryParams(BaseModel):
    page: int = 1
    page_size: int = 10
    search: str | None = None
    sort_by: str = "uploaded_at"
    order: str = "desc"