"""
Real SQLAlchemy ORM tables - previously the "Database" layer only existed
as an engine/session factory (app/core/database.py) with no actual table
definitions; leads.py used a plain in-memory dict instead. These are the
tables that dict should have been backed by all along.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid_str() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    leads: Mapped[list["LeadRecord"]] = relationship(back_populates="owner")


class LeadRecord(Base):
    """Named LeadRecord, not Lead, to avoid colliding with the existing
    Pydantic Lead schema in app/models/lead.py - that file owns the API
    request/response shapes, this one owns the actual table."""

    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    company: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="website")
    budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    timeline: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="new", index=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    agent_notes: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    owner: Mapped["User"] = relationship(back_populates="leads")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "source": self.source,
            "budget": self.budget,
            "timeline": self.timeline,
            "notes": self.notes,
            "status": self.status,
            "score": self.score,
            "agent_notes": self.agent_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
