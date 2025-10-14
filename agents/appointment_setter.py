from agno.agent import Agent
from agno.models.xai import xAI
from agno.tools import tool
import os

# Knowledge base path
KB_PATH = os.path.join(os.path.dirname(__file__), '..', 'knowledge_base')

@tool
def knowledge_query(topic: str) -> str:
    """Query the knowledge base for information on lead scoring, compliance, etc."""
    try:
        files = {
            'scoring': os.path.join(KB_PATH, 'lead_scoring_criteria.txt'),
            'compliance': os.path.join(KB_PATH, 'compliance_guidelines.txt'),
            'templates': os.path.join(KB_PATH, 'communication_templates.txt')
        }
        for key, path in files.items():
            if topic.lower() in key and os.path.exists(path):
                with open(path, 'r') as f:
                    return f.read()
        return "No relevant knowledge found."
    except Exception as e:
        return f"Knowledge query failed: {str(e)}"

# Custom tools
@tool
def monitoring(metric: str) -> dict:
    """Monitor engagement metrics in real-time."""
    try:
        # In production: Query analytics dashboard
        return {"engagement_score": 90, "metric": metric, "last_updated": "2025-09-11"}
    except Exception as e:
        return {"error": f"Monitoring failed: {str(e)}"}

@tool
def scheduling(details: dict) -> str:
    """Schedule appointments using calendar APIs."""
    try:
        # In production: Use Google Calendar API
        return f"Scheduled meeting for {details.get('lead', 'Unknown')} at {details.get('time', 'TBD')} (ID: CAL456)"
    except Exception as e:
        return f"Scheduling failed: {str(e)}"

@tool
def readiness_analyzer(signals: dict) -> bool:
    """Analyze readiness signals with ML."""
    try:
        # In production: Use trained model
        score = signals.get('score', 0)
        return score > 80
    except Exception as e:
        return False

appointment_setter = Agent(
    name="Appointment Setter",
    model=xAI(id="grok-4"),
    description="An AI agent focused on monitoring lead readiness and scheduling consultations with financial advisors.",
    instructions="""
Agent Responsibilities:
- Monitor 1000+ leads; schedule 200 appointments/week.
- Analyze signals for readiness; prioritize high-score leads.
- Coordinate with advisors; update CRM post-scheduling.
- Achieve 85% show-up rate; handle conflicts automatically.

Tool Usage Guidelines:
- Use knowledge_query for scheduling policies.
- Use monitoring for real-time metrics.
- Schedule with scheduling tool.
- Analyze readiness with readiness_analyzer.
""",
    tools=[knowledge_query, monitoring, scheduling, readiness_analyzer],
)