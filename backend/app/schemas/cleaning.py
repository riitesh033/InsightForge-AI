from typing import Any

from pydantic import BaseModel


class CleaningResponse(BaseModel):
    dataset_id: int
    original_filename: str
    cleaned_filename: str | None = None
    download_available: bool
    preview: dict[str, Any]