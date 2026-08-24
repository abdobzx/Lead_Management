"""
Analytics and reporting endpoints - scoped to the current authenticated
user's own leads (querying the real leads table, not a shared in-memory
dict every caller could see). Multi-tenant data isolation matters here:
before auth existed, every caller saw every other caller's leads.
"""

from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import time

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.pipeline_state import get_stats
from app.models.db_models import LeadRecord, User

router = APIRouter()


async def _current_user_leads(current_user: User, db: AsyncSession) -> list[LeadRecord]:
    result = await db.execute(select(LeadRecord).where(LeadRecord.owner_id == current_user.id))
    return list(result.scalars().all())


@router.get("/leads")
async def get_lead_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive lead analytics for the current user - computed from
    the real leads table, not fabricated. Returns zeros/empty for a user
    with no leads yet, the honest state, rather than a fake pre-filled
    dataset.
    """
    leads = await _current_user_leads(current_user, db)
    total = len(leads)
    scores = [lead.score for lead in leads if isinstance(lead.score, (int, float))]
    converted = sum(1 for lead in leads if lead.status == "converted")

    return {
        "total_leads": total,
        "qualified_leads": sum(1 for lead in leads if lead.status == "qualified"),
        "conversion_rate": round(converted / total * 100, 2) if total else 0.0,
        "average_score": round(sum(scores) / len(scores), 1) if scores else None,
        "leads_by_source": dict(Counter(lead.source or "unknown" for lead in leads)),
        "leads_by_status": dict(Counter(lead.status or "new" for lead in leads)),
        "generated_at": time.time(),
    }


@router.get("/agents")
async def get_agent_analytics(current_user: User = Depends(get_current_user)):
    """
    Get AI agent performance analytics - computed from real pipeline runs
    recorded via /leads/{id}/process, not fabricated. A stage with zero
    runs reports runs=0 and null averages rather than a fake number, since
    that's the honest state before anyone has actually run a lead through it.

    Note: pipeline stats are process-wide, not per-user, since the
    PipelineStats aggregator tracks agent behavior itself (token/latency
    cost per stage) rather than any one tenant's business data.
    """
    return get_stats().summary()


@router.get("/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get dashboard overview data for the current user - computed from the
    real leads table and real pipeline run stats. Historical
    week-over-week trend lines are not included: the schema doesn't yet
    retain the creation-time snapshots needed to compute them honestly,
    and a fabricated trend line would be worse than none.
    """
    leads = await _current_user_leads(current_user, db)
    total = len(leads)
    converted = sum(1 for lead in leads if lead.status == "converted")

    return {
        "summary": {
            "total_leads": total,
            "active_leads": sum(1 for lead in leads if lead.status not in ("converted", "lost")),
            "qualified_leads": sum(1 for lead in leads if lead.status == "qualified"),
            "converted_leads": converted,
            "conversion_rate": round(converted / total * 100, 2) if total else 0.0,
        },
        "agent_pipeline_stats": get_stats().summary(),
        "generated_at": time.time(),
    }
