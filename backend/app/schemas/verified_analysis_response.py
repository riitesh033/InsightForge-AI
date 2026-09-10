from pydantic import BaseModel

from app.schemas.analysis_report import VerifiedAnalysisReport
from app.schemas.insight import InsightReport


class VerifiedAnalysisResponse(BaseModel):
    analysis_id: int
    created_at: str

    verified_analysis: VerifiedAnalysisReport
    insights: InsightReport