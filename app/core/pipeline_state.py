"""
Shared, process-wide pipeline state: one PipelineStats instance that the
/leads/{id}/process endpoint records real runs into, and the
/analytics/agents endpoint reads real numbers back out of. Replaces what
used to be a hardcoded dict of fabricated statistics.
"""

from functools import lru_cache
from typing import Optional

from agents.orchestrator import LeadPipeline, PipelineStats

from app.core.config import settings

_stats = PipelineStats()


def get_stats() -> PipelineStats:
    return _stats


@lru_cache(maxsize=1)
def get_pipeline() -> Optional[LeadPipeline]:
    if not settings.ANTHROPIC_API_KEY:
        return None
    return LeadPipeline(api_key=settings.ANTHROPIC_API_KEY, stats=_stats)
