import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db import Base


def gen_id() -> str:
    return str(uuid.uuid4())


class Department(Base):
    __tablename__ = "departments"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, unique=True, nullable=False)
    headcount = Column(Integer, default=0)

    targets = relationship("Target", back_populates="department")


class Target(Base):
    """A simulated employee / recipient used for training (no real PII required)."""
    __tablename__ = "targets"

    id = Column(String, primary_key=True, default=gen_id)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    role = Column(String, nullable=False)
    seniority = Column(String, default="mid")  # junior | mid | senior | exec
    department_id = Column(String, ForeignKey("departments.id"))

    department = relationship("Department", back_populates="targets")


class GeneratedTemplate(Base):
    """An AI-generated phishing-awareness email template."""
    __tablename__ = "templates"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    html_body = Column(Text, nullable=False)
    target_role = Column(String)
    department = Column(String)
    seniority = Column(String)
    difficulty_level = Column(String, default="medium")  # easy | medium | hard
    model_used = Column(String)
    prompt_used = Column(Text)
    gophish_template_id = Column(Integer, nullable=True)  # set once pushed to Gophish
    created_at = Column(DateTime, default=datetime.utcnow)

    campaigns = relationship("Campaign", back_populates="template")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    template_id = Column(String, ForeignKey("templates.id"))
    department = Column(String)
    status = Column(String, default="draft")  # draft | approved | launched | completed
    approved_by = Column(String, nullable=True)  # required human-in-the-loop sign-off
    gophish_campaign_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    launched_at = Column(DateTime, nullable=True)

    template = relationship("GeneratedTemplate", back_populates="campaigns")
    events = relationship("ClickEvent", back_populates="campaign")


class ClickEvent(Base):
    """A single tracked interaction (sent / opened / clicked / submitted-data)."""
    __tablename__ = "click_events"

    id = Column(String, primary_key=True, default=gen_id)
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    target_email = Column(String, nullable=False)
    department = Column(String)
    event_type = Column(String, nullable=False)  # sent | opened | clicked | submitted_data
    occurred_at = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="events")


class FeedbackLog(Base):
    """Record of a personalized awareness micro-lesson delivered after a click."""
    __tablename__ = "feedback_logs"

    id = Column(String, primary_key=True, default=gen_id)
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    target_email = Column(String, nullable=False)
    lesson_html = Column(Text, nullable=False)
    model_used = Column(String)
    delivered = Column(Boolean, default=False)
    token = Column(String, unique=True, default=gen_id)
    created_at = Column(DateTime, default=datetime.utcnow)
