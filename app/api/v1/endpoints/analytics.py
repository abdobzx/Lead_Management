"""
Analytics and reporting endpoints.
"""

from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import time
from typing import Dict, Any

from app.core.database import get_db
from app.core.pipeline_state import get_stats
from app.api.v1.endpoints.leads import leads_db

router = APIRouter()


@router.get("/leads")
async def get_lead_analytics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive lead analytics - computed from the real in-memory
    leads_db (populated by POST /leads and /leads/{id}/process), not
    fabricated. Returns zeros/empty on a fresh instance with no leads yet,
    which is the honest state, rather than a fake pre-filled dataset.
    """
    leads = list(leads_db.values())
    total = len(leads)
    scores = [lead["score"] for lead in leads if isinstance(lead.get("score"), (int, float))]
    converted = sum(1 for lead in leads if lead.get("status") == "converted")

    return {
        "total_leads": total,
        "qualified_leads": sum(1 for lead in leads if lead.get("status") == "qualified"),
        "conversion_rate": round(converted / total * 100, 2) if total else 0.0,
        "average_score": round(sum(scores) / len(scores), 1) if scores else None,
        "leads_by_source": dict(Counter(lead.get("source", "unknown") for lead in leads)),
        "leads_by_status": dict(Counter(lead.get("status", "new") for lead in leads)),
        "generated_at": time.time(),
    }


@router.get("/agents")
async def get_agent_analytics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI agent performance analytics - computed from real pipeline runs
    recorded via /leads/{id}/process, not fabricated. A stage with zero
    runs reports runs=0 and null averages rather than a fake number, since
    that's the honest state before anyone has actually run a lead through it.
    """
    return get_stats().summary()


@router.get("/dashboard")
async def get_dashboard_data(
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard overview data - computed from the real in-memory
    leads_db and real pipeline run stats. Historical week-over-week trend
    lines are not included: this in-memory demo store doesn't retain the
    creation-time history needed to compute them honestly, and a fabricated
    trend line would be worse than none.
    """
    leads = list(leads_db.values())
    total = len(leads)
    converted = sum(1 for lead in leads if lead.get("status") == "converted")

    return {
        "summary": {
            "total_leads": total,
            "active_leads": sum(1 for lead in leads if lead.get("status") not in ("converted", "lost")),
            "qualified_leads": sum(1 for lead in leads if lead.get("status") == "qualified"),
            "converted_leads": converted,
            "conversion_rate": round(converted / total * 100, 2) if total else 0.0,
        },
        "agent_pipeline_stats": get_stats().summary(),
        "generated_at": time.time(),
    }