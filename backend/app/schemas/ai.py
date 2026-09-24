from pydantic import BaseModel, Field


class AIAnalysisRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=100)


class ResumeBulletsRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=100)
    tone: str = Field(default="professional", pattern="^(professional|concise|impact)$")


class AIReportOut(BaseModel):
    id: int
    report_type: str
    content: str

    model_config = {"from_attributes": True}
