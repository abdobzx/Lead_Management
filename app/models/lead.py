"""
Pydantic models for data validation and serialization.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class LeadStatus(str, Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    NURTURING = "nurturing"
    APPOINTMENT_SET = "appointment_set"
    CONVERTED = "converted"
    LOST = "lost"


class LeadSource(str, Enum):
    WEBSITE = "website"
    SOCIAL_MEDIA = "social_media"
    REFERRAL = "referral"
    COLD_CALL = "cold_call"
    EMAIL = "email"
    OTHER = "other"


class LeadBase(BaseModel):
    """Base lead model."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = Field(None, max_length=100)
    source: LeadSource = LeadSource.WEBSITE
    budget: Optional[float] = Field(None, gt=0)
    timeline: Optional[str] = None
    notes: Optional[str] = None


class LeadCreate(LeadBase):
    """Model for creating a new lead."""
    pass


class LeadUpdate(BaseModel):
    """Model for updating a lead."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = Field(None, max_length=100)
    source: Optional[LeadSource] = None
    status: Optional[LeadStatus] = None
    score: Optional[int] = Field(None, ge=0, le=100)
    budget: Optional[float] = Field(None, gt=0)
    timeline: Optional[str] = None
    notes: Optional[str] = None
    agent_notes: Optional[Dict[str, Any]] = None


class Lead(LeadBase):
    """Complete lead model."""
    id: str
    status: LeadStatus = LeadStatus.NEW
    score: int = 0
    created_at: datetime
    updated_at: datetime
    agent_notes: Optional[Dict[str, Any]] = None
    processed_by: Optional[str] = None
    processing_history: Optional[list] = None


class LeadProcessRequest(BaseModel):
    """Request model for processing a lead."""
    priority: Optional[str] = "normal"  # normal, high, urgent
    custom_instructions: Optional[str] = None


class LeadProcessResponse(BaseModel):
    """Response model for lead processing."""
    lead_id: str
    status: str
    score: int
    recommendation: str
    processing_time: float
    agent_responses: Dict[str, Any]


class AnalyticsSummary(BaseModel):
    """Summary analytics model."""
    total_leads: int
    qualified_leads: int
    conversion_rate: float
    average_score: float
    generated_at: datetime


class AgentPerformance(BaseModel):
    """Agent performance metrics."""
    agent_name: str
    leads_processed: int
    success_rate: float
    average_processing_time: float
    accuracy_score: Optional[float] = None


class HealthCheck(BaseModel):
    """Health check response model."""
    status: str
    timestamp: float
    version: Optional[str] = None
    checks: Optional[Dict[str, str]] = None