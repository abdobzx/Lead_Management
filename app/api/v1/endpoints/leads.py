"""
Leads management endpoints - backed by the real leads table (see
app/models/db_models.py), scoped per-authenticated-user via owner_id.
Previously this was a plain in-memory dict shared across every caller,
with no auth at all and data lost on every restart.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.pipeline_state import get_pipeline
from app.models.db_models import LeadRecord, User

router = APIRouter()


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


async def _get_owned_lead(lead_id: str, current_user: User, db: AsyncSession) -> LeadRecord:
    result = await db.execute(
        select(LeadRecord).where(LeadRecord.id == lead_id, LeadRecord.owner_id == current_user.id)
    )
    lead = result.scalar_one_or_none()
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.get("/")
async def get_leads(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's leads, paginated."""
    result = await db.execute(
        select(LeadRecord)
        .where(LeadRecord.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    leads = result.scalars().all()

    count_result = await db.execute(select(LeadRecord).where(LeadRecord.owner_id == current_user.id))
    total = len(count_result.scalars().all())

    return {"leads": [lead.to_dict() for lead in leads], "total": total}


@router.post("/")
async def create_lead(
    lead_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new lead owned by the current user."""
    lead = LeadRecord(owner_id=current_user.id, status="new", **lead_data)
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead.to_dict()


@router.get("/{lead_id}")
async def get_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead = await _get_owned_lead(lead_id, current_user, db)
    return lead.to_dict()


@router.put("/{lead_id}")
async def update_lead(
    lead_id: str,
    lead_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead = await _get_owned_lead(lead_id, current_user, db)
    for key, value in lead_data.items():
        if hasattr(lead, key):
            setattr(lead, key, value)
    await db.commit()
    await db.refresh(lead)
    return lead.to_dict()


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead = await _get_owned_lead(lead_id, current_user, db)
    await db.delete(lead)
    await db.commit()
    return {"message": "Lead deleted"}


@router.post("/{lead_id}/process")
async def process_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Process a lead through the real 6-agent pipeline (lead_generator ->
    qualification_agent -> crm_manager -> nurturing_specialist ->
    appointment_setter -> reporting_analytics_agent), each handoff using a
    reason-first, faithful-extraction pass rather than raw passthrough.
    """
    lead = await _get_owned_lead(lead_id, current_user, db)

    pipeline = get_pipeline()
    if pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY is not configured - the agent pipeline cannot run.",
        )

    lead.status = "processing"
    await db.commit()

    result = pipeline.process_lead(lead.to_dict())

    lead.status = result.final_status
    lead.agent_notes = {
        stage.stage: {
            "summary": stage.content.get("summary"),
            "key_values": stage.content.get("key_values"),
            "error": stage.error,
        }
        for stage in result.stages
    }
    score = _extract_score(result.stages)
    if score is not None:
        lead.score = score

    await db.commit()

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
