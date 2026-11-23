from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TemplateGenerateRequest(BaseModel):
    target_role: str
    department: str
    seniority: str = "mid"
    company_context: str = "a mid-size tech company"
    difficulty_level: str = "medium"  # easy | medium | hard
    push_to_gophish: bool = False


class TemplateOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: str
    name: str
    subject: str
    html_body: str
    target_role: Optional[str]
    department: Optional[str]
    seniority: Optional[str]
    difficulty_level: Optional[str]
    model_used: Optional[str]
    gophish_template_id: Optional[int]
    created_at: datetime


class CampaignCreateRequest(BaseModel):
    name: str
    template_id: str
    department: str


class CampaignApproveRequest(BaseModel):
    approved_by: str


class CampaignOut(BaseModel):
    id: str
    name: str
    template_id: str
    department: Optional[str]
    status: str
    approved_by: Optional[str]
    created_at: datetime
    launched_at: Optional[datetime]

    class Config:
        from_attributes = True


class ClickEventIn(BaseModel):
    campaign_id: str
    target_email: str
    department: str
    event_type: str  # sent | opened | clicked | submitted_data


class AnalyticsSummaryRow(BaseModel):
    department: str
    sent: int
    opened: int
    clicked: int
    submitted_data: int
    click_rate_pct: float


class FeedbackTriggerRequest(BaseModel):
    campaign_id: str
    target_email: str
    target_role: str = "employee"
