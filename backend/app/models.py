from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ContactType(str, enum.Enum):
    buyer = "Buyer"
    influencer = "Influencer"
    gatekeeper = "Gatekeeper"
    technical_validator = "Technical Validator"


class OutreachStatus(str, enum.Enum):
    not_contacted = "Not contacted"
    message_sent = "Message sent"
    replied = "Replied"
    meeting_booked = "Meeting booked"
    not_relevant = "Not relevant"


class OutreachDraftStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    sent = "sent"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    done = "done"
    dismissed = "dismissed"


class PipelineStage(Base):
    __tablename__ = "pipeline_stages"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    order_index = Column(Integer, nullable=False)
    color = Column(String(20), nullable=False, default="#00C9A7")

    companies = relationship("Company", back_populates="pipeline_stage")


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    industry = Column(String(100))
    website = Column(String(500))
    country = Column(String(100))
    notes = Column(Text)
    status = Column(String(50), default="active")
    pipeline_stage_id = Column(Integer, ForeignKey("pipeline_stages.id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    pipeline_stage = relationship("PipelineStage", back_populates="companies")
    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")
    research_reports = relationship("ResearchReport", back_populates="company", cascade="all, delete-orphan")
    signal_briefs = relationship("SignalBrief", back_populates="company", cascade="all, delete-orphan")
    outreach_drafts = relationship("OutreachDraft", back_populates="company", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="company", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(200), nullable=False)
    role = Column(String(100))
    email = Column(String(200))
    linkedin_url = Column(String(500))
    contact_type = Column(SAEnum(ContactType), default=ContactType.buyer)
    notes = Column(Text)
    outreach_status = Column(SAEnum(OutreachStatus), default=OutreachStatus.not_contacted)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    company = relationship("Company", back_populates="contacts")
    outreach_drafts = relationship("OutreachDraft", back_populates="contact", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="contact")


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    overview = Column(Text)
    signals = Column(Text)  # JSON string
    cashflow_pressures = Column(Text)  # JSON string
    buyer_personas = Column(Text)  # JSON string
    outreach_angle = Column(Text)
    confidence_score = Column(Float, default=0.0)
    source_links = Column(Text)  # JSON string
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    company = relationship("Company", back_populates="research_reports")
    signal_briefs = relationship("SignalBrief", back_populates="research", cascade="all, delete-orphan")


class SignalBrief(Base):
    __tablename__ = "signal_briefs"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    research_id = Column(Integer, ForeignKey("research_reports.id"))
    executive_signal = Column(Text)
    why_it_matters = Column(Text)
    receivables_blind_spots = Column(Text)  # JSON string
    operational_impact = Column(Text)
    suggested_action = Column(Text)
    conversation_opener = Column(Text)
    is_edited = Column(Boolean, default=False)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    company = relationship("Company", back_populates="signal_briefs")
    research = relationship("ResearchReport", back_populates="signal_briefs")
    outreach_drafts = relationship("OutreachDraft", back_populates="brief", cascade="all, delete-orphan")


class OutreachDraft(Base):
    __tablename__ = "outreach_drafts"

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    company_id = Column(Integer, ForeignKey("companies.id"))
    brief_id = Column(Integer, ForeignKey("signal_briefs.id"))
    linkedin_message = Column(Text)
    email_subject = Column(Text)
    email_body = Column(Text)
    followup_message = Column(Text)
    gatekeeper_version = Column(Text)
    technical_validator_version = Column(Text)
    status = Column(SAEnum(OutreachDraftStatus), default=OutreachDraftStatus.draft)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    contact = relationship("Contact", back_populates="outreach_drafts")
    company = relationship("Company", back_populates="outreach_drafts")
    brief = relationship("SignalBrief", back_populates="outreach_drafts")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    description = Column(Text, nullable=False)
    due_date = Column(DateTime)
    status = Column(SAEnum(TaskStatus), default=TaskStatus.pending)
    task_type = Column(String(100))
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    company = relationship("Company", back_populates="tasks")
    contact = relationship("Contact", back_populates="tasks")
