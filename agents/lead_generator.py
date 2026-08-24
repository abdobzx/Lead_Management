from agno.agent import Agent
from agno.models.anthropic import Claude
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
def web_search(query: str) -> str:
    """Search the web for lead sources using real-time data."""
    try:
        # In production: Use requests to search APIs like Google or social media
        return f"Real-time search results for '{query}': [Simulated leads from LinkedIn, Twitter, etc.]"
    except Exception as e:
        return f"Search failed: {str(e)}"

@tool
def data_enrichment(lead_data: dict) -> dict:
    """Enrich lead data with financial details using external APIs."""
    try:
        # In production: Call credit bureaus, property APIs
        lead_data['credit_score'] = 750  # Simulated
        lead_data['property_value'] = 450000
        return lead_data
    except Exception as e:
        return {"error": f"Enrichment failed: {str(e)}"}

lead_generator = Agent(
    name="Lead Generator",
    model=Claude(id="claude-haiku-4-5-20251001"),
    description="An AI agent focused on capturing and enriching leads from multiple channels to build a robust pipeline for financial sales.",
    instructions="""
Agent Responsibilities:
- Capture leads from portals, social media, and public records with high accuracy (>90% success rate).
- Enrich profiles with financial details using verified sources.
- Ensure compliance with GDPR/CCPA; log all data sources.
- Pass enriched leads to Qualification Agent; aim for 100 leads/day in production.

Tool Usage Guidelines:
- Use knowledge_query for compliance and scoring info.
- Use web_search for real-time lead discovery.
- Apply data_enrichment for accurate financial data.
- Handle errors by retrying or escalating.
""",
    tools=[knowledge_query, web_search, data_enrichment],
)