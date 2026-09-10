from typing import Literal

from pydantic import BaseModel, Field


Priority = Literal[
    "Critical",
    "High",
    "Medium",
    "Low",
]


class InsightEvidence(BaseModel):
    metric: str
    value: str
    context: str | None = None


class ProfessionalInsight(BaseModel):
    """
    A single evidence-based analytical insight.

    This object separates factual evidence from interpretation
    and recommended action.
    """

    category: str

    title: str

    finding: str

    evidence: list[InsightEvidence] = Field(
        default_factory=list
    )

    interpretation: str

    potential_impact: str

    recommended_action: str

    priority: Priority

    confidence: Literal[
        "High",
        "Medium",
        "Low",
    ] = "High"


class InsightReport(BaseModel):
    """
    Complete structured insight output.
    """

    insights: list[ProfessionalInsight] = Field(
        default_factory=list
    )

    top_findings: list[ProfessionalInsight] = Field(
        default_factory=list
    )

    top_actions: list[ProfessionalInsight] = Field(
        default_factory=list
    )