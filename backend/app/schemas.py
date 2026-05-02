from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, field_validator
import json


# ── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Pipeline Stages ───────────────────────────────────────────────────────────

class PipelineStageBase(BaseModel):
    name: str
    order_index: int
    color: str = "#00C9A7"


class PipelineStageOut(PipelineStageBase):
    id: int
    model_config = {"from_attributes": True}


# ── Company ───────────────────────────────────────────────────────────────────

class CompanyCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "active"
    pipeline_stage_id: Optional[int] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    pipeline_stage_id: Optional[int] = None


class CompanyOut(BaseModel):
    id: int
    name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    pipeline_stage_id: Optional[int] = None
    pipeline_stage: Optional[PipelineStageOut] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class CompanyListOut(CompanyOut):
    research_count: int = 0
    brief_count: int = 0
    contact_count: int = 0


# ── Contact ───────────────────────────────────────────────────────────────────

class ContactCreate(BaseModel):
    company_id: int
    name: str
    role: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    contact_type: Optional[str] = "Buyer"
    notes: Optional[str] = None
    outreach_status: Optional[str] = "Not contacted"


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    contact_type: Optional[str] = None
    notes: Optional[str] = None
    outreach_status: Optional[str] = None


class ContactOut(BaseModel):
    id: int
    company_id: int
    name: str
    role: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    contact_type: Optional[str] = None
    notes: Optional[str] = None
    outreach_status: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Research ──────────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    company_name: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None


class ResearchOut(BaseModel):
    id: int
    company_id: int
    overview: Optional[str] = None
    signals: Optional[List[str]] = None
    cashflow_pressures: Optional[List[str]] = None
    buyer_personas: Optional[List[Any]] = None
    outreach_angle: Optional[str] = None
    confidence_score: Optional[float] = None
    source_links: Optional[List[str]] = None
    is_demo: bool = False
    created_at: datetime

    @classmethod
    def from_orm(cls, obj):
        data = {
            "id": obj.id,
            "company_id": obj.company_id,
            "overview": obj.overview,
            "outreach_angle": obj.outreach_angle,
            "confidence_score": obj.confidence_score,
            "is_demo": obj.is_demo,
            "created_at": obj.created_at,
            "signals": _parse_json_field(obj.signals, []),
            "cashflow_pressures": _parse_json_field(obj.cashflow_pressures, []),
            "buyer_personas": _parse_json_field(obj.buyer_personas, []),
            "source_links": _parse_json_field(obj.source_links, []),
        }
        return cls(**data)

    model_config = {"from_attributes": True}


# ── Signal Brief ──────────────────────────────────────────────────────────────

class BriefGenerateRequest(BaseModel):
    research_id: int


class BriefUpdate(BaseModel):
    executive_signal: Optional[str] = None
    why_it_matters: Optional[str] = None
    receivables_blind_spots: Optional[List[str]] = None
    operational_impact: Optional[str] = None
    suggested_action: Optional[str] = None
    conversation_opener: Optional[str] = None


class BriefOut(BaseModel):
    id: int
    company_id: int
    research_id: Optional[int] = None
    executive_signal: Optional[str] = None
    why_it_matters: Optional[str] = None
    receivables_blind_spots: Optional[List[str]] = None
    operational_impact: Optional[str] = None
    suggested_action: Optional[str] = None
    conversation_opener: Optional[str] = None
    is_edited: bool = False
    is_demo: bool = False
    created_at: datetime

    @classmethod
    def from_orm(cls, obj):
        data = {
            "id": obj.id,
            "company_id": obj.company_id,
            "research_id": obj.research_id,
            "executive_signal": obj.executive_signal,
            "why_it_matters": obj.why_it_matters,
            "operational_impact": obj.operational_impact,
            "suggested_action": obj.suggested_action,
            "conversation_opener": obj.conversation_opener,
            "is_edited": obj.is_edited,
            "is_demo": obj.is_demo,
            "created_at": obj.created_at,
            "receivables_blind_spots": _parse_json_field(obj.receivables_blind_spots, []),
        }
        return cls(**data)

    model_config = {"from_attributes": True}


# ── Outreach ──────────────────────────────────────────────────────────────────

class OutreachGenerateRequest(BaseModel):
    contact_id: int
    company_id: int
    brief_id: Optional[int] = None
    tone: Optional[str] = "professional"


class OutreachDraftOut(BaseModel):
    id: int
    contact_id: Optional[int] = None
    company_id: Optional[int] = None
    brief_id: Optional[int] = None
    linkedin_message: Optional[str] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    followup_message: Optional[str] = None
    gatekeeper_version: Optional[str] = None
    technical_validator_version: Optional[str] = None
    status: Optional[str] = None
    is_demo: bool = False
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Task ──────────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    company_id: Optional[int] = None
    contact_id: Optional[int] = None
    description: str
    due_date: Optional[datetime] = None
    task_type: Optional[str] = None


class TaskUpdate(BaseModel):
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    task_type: Optional[str] = None


class TaskOut(BaseModel):
    id: int
    company_id: Optional[int] = None
    contact_id: Optional[int] = None
    description: str
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    task_type: Optional[str] = None
    is_demo: bool = False
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_companies: int
    companies_researched: int
    contacts_added: int
    outreach_drafts: int
    calls_booked: int
    briefs_generated: int
    pipeline_value: str = "$0"
    today_tasks: List[TaskOut] = []


# ── Admin ─────────────────────────────────────────────────────────────────────

class HealthStatus(BaseModel):
    api: str
    database: str
    ai: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_json_field(value, default):
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


# ── Web Intelligence ──────────────────────────────────────────────────────────

class IntelligenceScanTriggerResponse(BaseModel):
    message: str
    status: str


class IntelligenceStatusResponse(BaseModel):
    status: str   # pending|running|complete|failed|not_scanned
    completed_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    error: Optional[str] = None


class WebIntelligenceOut(BaseModel):
    id: int
    scan_status: str
    scan_triggered_by: Optional[str] = None
    scan_started_at: Optional[datetime] = None
    scan_completed_at: Optional[datetime] = None
    scan_error: Optional[str] = None
    is_jse_listed: bool = False
    jse_ticker: Optional[str] = None
    latest_stock_data: Optional[Any] = None
    news_articles: List[Any] = []
    sens_announcements: List[Any] = []
    leadership_mentions: List[Any] = []
    linkedin_company_url: Optional[str] = None
    leadership_page_url: Optional[str] = None
    intelligence_summary: Optional[str] = None
    key_signals: List[Any] = []
    timing_assessment: Optional[str] = None
    recommended_approach: Optional[str] = None
    is_demo: bool = False
    created_at: datetime
    model_config = {"from_attributes": True}


class ContactDiscoveryOut(BaseModel):
    id: int
    recommended_roles: List[Any] = []
    recommended_departments: List[Any] = []
    linkedin_search_urls: List[Any] = []
    linkedin_company_page: Optional[str] = None
    contact_sources: List[Any] = []
    publicly_listed_contacts: List[Any] = []
    is_demo: bool = False
    created_at: datetime
    model_config = {"from_attributes": True}


class IntelligenceResponse(BaseModel):
    intelligence: Optional[WebIntelligenceOut] = None
    discovery: Optional[ContactDiscoveryOut] = None


# ── Outreach (extended) ───────────────────────────────────────────────────────

class OutreachGenerateRequestV2(OutreachGenerateRequest):
    """Extended outreach request supporting web intelligence source."""
    web_intelligence_id: Optional[int] = None
    source: Optional[str] = "brief"   # brief | web | all
