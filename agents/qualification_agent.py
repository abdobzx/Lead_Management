from agno.agent import Agent
from agno.models.xai import xAI
from agno.tools import tool
import os
import pandas as pd

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
def data_analysis(lead_data: dict) -> dict:
    """Analyze lead data for scoring using data science techniques."""
    try:
        # In production: Use pandas for analysis
        df = pd.DataFrame([lead_data])
        score = (df['income'].iloc[0] // 1000) + (df['credit_score'].iloc[0] // 10)
        lead_data['score'] = min(score, 100)
        return lead_data
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

@tool
def database_query(query: str) -> list:
    """Query lead database for historical data."""
    try:
        # In production: Connect to SQL/NoSQL DB
        return [{"id": 1, "name": "John Doe", "status": "qualified", "score": 85}]
    except Exception as e:
        return [{"error": f"Query failed: {str(e)}"}]

@tool
def financial_scoring(data: dict) -> float:
    """Advanced financial scoring for capacity."""
    try:
        # In production: Use ML model
        base_score = data.get('income', 0) * 0.01 + data.get('credit_score', 0) * 0.1
        return min(base_score, 100.0)
    except Exception as e:
        return 0.0

qualification_agent = Agent(
    name="Qualification Agent",
    model=xAI(id="grok-4"),
    description="An AI agent focused on scoring and qualifying leads based on financial capacity and readiness for buying/selling.",
    instructions="""
Agent Responsibilities:
- Score leads using financial metrics; achieve >80% qualification accuracy.
- Qualify leads for products like loans/investments; reject <50 score leads.
- Trigger follow-ups for unqualified; maintain audit logs.
- Process 50 leads/hour in production; optimize for speed and precision.

Tool Usage Guidelines:
- Use knowledge_query for scoring criteria.
- Use data_analysis for statistical scoring.
- Query database_query for lead history.
- Apply financial_scoring for advanced models.
""",
    tools=[knowledge_query, data_analysis, database_query, financial_scoring],
)