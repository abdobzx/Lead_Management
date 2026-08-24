"""
Leads management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.core.pipeline_state import get_pipeline

router = APIRouter()


# In-memory storage for demo (replace with database models later)
leads_db = {}


_SCORE_KEY_PRIORITY = ("financialcapacityscore", "capacityscore", "qualificationscore")


def _normalize_key(key: str) -> str:
    return "".join(ch for ch in key.lower() if ch.isalnum())


def _extract_score(stages) -> Optional[int]:
    """Pull the 0-100 lead-qualification score out of whichever stage
    reported one. Matches key names loosely (case/spacing/underscore
    insensitive) since the extraction step's key_values dict has no fixed
    schema - the same fact can come back as "financial_capacity_score" one
    run and "Financial Capacity Score" the next. Deliberately excludes
    "credit_score" and similar - those are on a different scale (e.g.
    300-850) and would silently corrupt this field if matched by a
    generic "contains 'score'" check."""
    key_values_by_stage = [stage.content.get("key_values", {}) for stage in stages]

    for preferred_key in _SCORE_KEY_PRIORITY:
        for key_values in key_values_by_stage:
            for actual_key, value in key_values.items():
                if _normalize_key(actual_key) != preferred_key:
                    continue
                try:
                    return int(float(str(value).split("/")[0].strip()))
                except (ValueError, IndexError):
                    continue
    return None


@router.get("/")
async def get_leads(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all leads with pagination.
    """
    leads = list(leads_db.values())[skip:skip + limit]
    return {"leads": leads, "total": len(leads_db)}


@router.post("/")
async def create_lead(
    lead_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new lead.
    """
    lead_id = str(uuid.uuid4())
    lead = {
        "id": lead_id,
        "status": "new",
        "score": 0,
        **lead_data
    }
    leads_db[lead_id] = lead
    return lead


@router.get("/{lead_id}")
async def get_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific lead by ID.
    """
    if lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead not found")
    return leads_db[lead_id]


@router.put("/{lead_id}")
async def update_lead(
    lead_id: str,
    lead_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a lead.
    """
    if lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead not found")

    leads_db[lead_id].update(lead_data)
    return leads_db[lead_id]


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a lead.
    """
    if lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead not found")

    del leads_db[lead_id]
    return {"message": "Lead deleted"}


@router.post("/{lead_id}/process")
async def process_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Process a lead through the real 6-agent pipeline (lead_generator ->
    qualification_agent -> crm_manager -> nurturing_specialist ->
    appointment_setter -> reporting_analytics_agent), each handoff using a
    reason-first, faithful-extraction pass rather than raw passthrough.
    """
    if lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead not found")

    pipeline = get_pipeline()
    if pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY is not configured - the agent pipeline cannot run.",
        )

    lead = leads_db[lead_id]
    lead["status"] = "processing"

    result = pipeline.process_lead(lead)

    lead["status"] = result.final_status
    lead["agent_notes"] = {
        stage.stage: {
            "summary": stage.content.get("summary"),
            "key_values": stage.content.get("key_values"),
            "error": stage.error,
        }
        for stage in result.stages
    }
    score = _extract_score(result.stages)
    if score is not None:
        lead["score"] = score

    return {
        "lead_id": lead_id,
        "status": result.final_status,
        "succeeded": result.succeeded,
        "stages": [
            {
                "stage": s.stage,
                "summary": s.content.get("summary"),
                "status": s.content.get("status"),
                "error": s.error,
                "duration_seconds": s.duration_seconds,
            }
            for s in result.stages
        ],
    }