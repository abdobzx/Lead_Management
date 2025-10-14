"""
Leads management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid

from app.core.database import get_db

router = APIRouter()


# In-memory storage for demo (replace with database models later)
leads_db = {}


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
    Process a lead through the AI agent pipeline.
    """
    if lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead not found")

    # TODO: Integrate with actual agent processing
    lead = leads_db[lead_id]
    lead["status"] = "processing"

    # Simulate processing
    lead["score"] = 75  # Mock score
    lead["status"] = "qualified"

    return {
        "lead_id": lead_id,
        "status": "processed",
        "score": lead["score"],
        "recommendation": "high_priority"
    }