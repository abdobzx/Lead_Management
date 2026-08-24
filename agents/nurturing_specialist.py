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
def email_sms(content: str, recipient: str) -> str:
    """Send emails or SMS using production APIs."""
    try:
        # In production: Use SendGrid or Twilio
        return f"Message sent to {recipient}: {content[:100]}... (ID: MSG123)"
    except Exception as e:
        return f"Send failed: {str(e)}"

@tool
def content_generation(topic: str) -> str:
    """Generate personalized content using AI."""
    try:
        # In production: Use GPT for generation
        return f"Generated content on {topic}: [AI-generated insights on market trends]"
    except Exception as e:
        return f"Generation failed: {str(e)}"

@tool
def nurturing_sequence_builder(segment: str) -> list:
    """Build nurturing sequences with analytics."""
    try:
        # In production: Use templates and A/B testing
        return [f"Email 1: Intro for {segment}", "Email 2: Follow-up tips", "Email 3: Call to action"]
    except Exception as e:
        return [f"Error building sequence: {str(e)}"]

nurturing_specialist = Agent(
    name="Nurturing Specialist",
    model=Claude(id="claude-haiku-4-5-20251001"),
    description="An AI agent focused on developing and executing automated nurturing campaigns with personalized financial content.",
    instructions="""
Agent Responsibilities:
- Generate content for 500+ leads/week; achieve 70% open rates.
- Execute sequences; monitor engagement and adjust dynamically.
- Pass engaged leads (>80% engagement) to Appointment Setter.
- Comply with CAN-SPAM; personalize 100% of communications.

Tool Usage Guidelines:
- Use knowledge_query for templates and compliance.
- Use email_sms for sending via APIs.
- Generate content with content_generation.
- Build sequences with nurturing_sequence_builder.
""",
    tools=[knowledge_query, email_sms, content_generation, nurturing_sequence_builder],
)