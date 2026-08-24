"""
The actual sequential agent pipeline the README describes - previously
just a mermaid diagram with no code behind it. Each of the 6 agents
(lead_generator, qualification_agent, crm_manager, nurturing_specialist,
appointment_setter, reporting_analytics_agent) is a real Agno Agent, but
running them isn't enough on its own: naively passing one agent's raw text
response straight into the next agent's prompt is exactly the "naive JSON
handoff" pattern shown (see the reasonrelay project) to lose specific
facts under compression, especially numbers and thresholds that competing
details can bury.

This orchestrator applies the same reason-first, faithful-extraction,
provenance-carrying handoff pattern between every stage: each agent
produces its full response, then a lightweight second pass restates the
specific facts the next agent actually needs - instructed explicitly not
to invent caveats or drop precision - before that gets folded into the
next agent's prompt. Real per-stage token/latency metrics are recorded
from Agno's own RunOutput.metrics, not fabricated.
"""

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from anthropic import Anthropic

from .appointment_setter import appointment_setter
from .crm_manager import crm_manager
from .lead_generator import lead_generator
from .nurturing_specialist import nurturing_specialist
from .qualification_agent import qualification_agent
from .reporting_analytics_agent import reporting_analytics_agent

EXTRACTION_MODEL = "claude-haiku-4-5-20251001"

STAGES = [
    ("lead_generator", lead_generator),
    ("qualification_agent", qualification_agent),
    ("crm_manager", crm_manager),
    ("nurturing_specialist", nurturing_specialist),
    ("appointment_setter", appointment_setter),
    ("reporting_analytics_agent", reporting_analytics_agent),
]

VALID_LEAD_STATUSES = {"new", "qualified", "nurturing", "appointment_set", "converted", "lost"}

HANDOFF_SCHEMA = (
    '{"summary": "<2-3 sentence faithful summary of this stage\'s outcome>", '
    '"key_values": {"<fact name>": "<exact value>", ...}, '
    '"status": "<exactly one of: new, qualified, nurturing, appointment_set, converted, lost - '
    "the lead's overall pipeline status matching this app's LeadStatus enum, "
    'not a free-text description of this stage>"}'
)


@dataclass
class StageResult:
    stage: str
    reasoning_trace: str
    content: dict
    provenance: list = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    duration_seconds: float = 0.0
    error: Optional[str] = None


@dataclass
class PipelineResult:
    lead_id: str
    stages: list = field(default_factory=list)  # list[StageResult]
    final_status: str = "new"

    @property
    def succeeded(self) -> bool:
        return all(s.error is None for s in self.stages)


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    else:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)
    return json.loads(text)


class PipelineStats:
    """Real, measured per-agent stats accumulated across actual pipeline
    runs - replaces the hardcoded fake numbers the /analytics/agents
    endpoint used to return. Empty/zero until real runs have happened,
    which is the honest behavior."""

    def __init__(self) -> None:
        self._runs: dict[str, list[StageResult]] = {name: [] for name, _ in STAGES}

    def record(self, result: StageResult) -> None:
        self._runs[result.stage].append(result)

    def summary(self) -> dict:
        out = {}
        for name, results in self._runs.items():
            if not results:
                out[name] = {
                    "runs": 0,
                    "success_rate": None,
                    "avg_duration_seconds": None,
                    "avg_input_tokens": None,
                    "avg_output_tokens": None,
                }
                continue
            n = len(results)
            successes = sum(1 for r in results if r.error is None)
            out[name] = {
                "runs": n,
                "success_rate": round(successes / n, 3),
                "avg_duration_seconds": round(sum(r.duration_seconds for r in results) / n, 3),
                "avg_input_tokens": round(sum(r.input_tokens for r in results) / n, 1),
                "avg_output_tokens": round(sum(r.output_tokens for r in results) / n, 1),
            }
        return out


class LeadPipeline:
    def __init__(self, api_key: str, stats: Optional[PipelineStats] = None):
        self.extraction_client = Anthropic(api_key=api_key)
        self.stats = stats if stats is not None else PipelineStats()

    def _extract_handoff(self, stage_name: str, raw_response: str, lead_context: dict) -> tuple[dict, float]:
        """The reason-first, faithful-extraction second pass - reuses the
        exact validated prompt pattern from reasonrelay/relay.py's
        _run_reasonrelay, adapted to this pipeline's stage output."""
        prompt = (
            f"You are extracting a handoff summary from the '{stage_name}' stage of a lead "
            "processing pipeline, for the next stage to consume. Faithfully restate every "
            "specific fact - numbers, scores, thresholds, statuses - exactly as given below. "
            "Do not add caveats, ambiguities, or uncertainty that is not explicitly present. "
            "Do not speculate about what might be missing.\n\n"
            f"Lead context: {json.dumps(lead_context, default=str)}\n\n"
            f"Stage output:\n{raw_response}\n\n"
            f"Extract into this JSON schema:\n{HANDOFF_SCHEMA}\n\n"
            "Return ONLY the JSON object, no other text."
        )
        start = time.time()
        response = self.extraction_client.messages.create(
            model=EXTRACTION_MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        duration = time.time() - start
        return _parse_json_response(response.content[0].text), duration

    def process_lead(self, lead: dict) -> PipelineResult:
        result = PipelineResult(lead_id=str(lead.get("id", "unknown")))
        previous_handoff: Optional[dict] = None
        provenance: list = []

        for stage_name, agent in STAGES:
            stage_start = time.time()
            try:
                prompt_parts = [f"Process this lead: {json.dumps(lead, default=str)}"]
                if previous_handoff is not None:
                    prompt_parts.append(
                        f"\nPrevious stage ({result.stages[-1].stage}) handoff:\n"
                        f"{json.dumps(previous_handoff, default=str)}"
                    )
                run_output = agent.run("\n".join(prompt_parts))
                raw_response = run_output.get_content_as_string()

                extracted, extract_duration = self._extract_handoff(stage_name, raw_response, lead)
                provenance.append(f"{stage_name}: {extracted.get('summary', '')}")

                stage_result = StageResult(
                    stage=stage_name,
                    reasoning_trace=raw_response,
                    content=extracted,
                    provenance=list(provenance),
                    input_tokens=(run_output.metrics.input_tokens if run_output.metrics else 0),
                    output_tokens=(run_output.metrics.output_tokens if run_output.metrics else 0),
                    duration_seconds=round(time.time() - stage_start, 3),
                )
                previous_handoff = extracted
                candidate_status = extracted.get("status")
                if candidate_status in VALID_LEAD_STATUSES:
                    result.final_status = candidate_status
            except Exception as exc:  # noqa: BLE001 - record the failure, keep going isn't safe here, so stop
                stage_result = StageResult(
                    stage=stage_name,
                    reasoning_trace="",
                    content={},
                    duration_seconds=round(time.time() - stage_start, 3),
                    error=str(exc),
                )
                result.stages.append(stage_result)
                self.stats.record(stage_result)
                break

            result.stages.append(stage_result)
            self.stats.record(stage_result)

        return result
