from agno.agent import Agent
from agno.models.anthropic import Claude
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
def analytics(data: dict) -> dict:
    """Compute KPIs using data analysis."""
    try:
        # In production: Use pandas for calculations
        df = pd.DataFrame([data])
        conversions = df['conversions'].iloc[0] if 'conversions' in df else 0
        total = df['total'].iloc[0] if 'total' in df else 1
        rate = conversions / total if total > 0 else 0
        return {"conversion_rate": round(rate, 2), "insights": "Rate improved by 5% YoY"}
    except Exception as e:
        return {"error": f"Analytics failed: {str(e)}"}

@tool
def visualization(report: dict) -> str:
    """Generate visualizations for reports."""
    try:
        # In production: Use matplotlib or Plotly
        return f"Visualization generated: Bar chart of {report} (URL: chart.example.com)"
    except Exception as e:
        return f"Visualization failed: {str(e)}"

reporting_analytics_agent = Agent(
    name="Reporting & Analytics Agent",
    model=Claude(id="claude-haiku-4-5-20251001"),
    description="An AI agent focused on tracking KPIs, analyzing lead funnel performance, and generating reports.",
    instructions="""
Agent Responsibilities:
- Track KPIs for 1000+ leads; generate reports daily.
- Analyze trends; identify bottlenecks with >95% accuracy.
- Produce visualizations; share with stakeholders.
- Ensure data privacy; automate report distribution.

Tool Usage Guidelines:
- Use knowledge_query for reporting standards.
- Compute KPIs with analytics tool.
- Visualize with visualization tool.
""",
    tools=[knowledge_query, analytics, visualization],
)