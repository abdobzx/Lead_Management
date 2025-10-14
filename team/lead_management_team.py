from agents.lead_generator import lead_generator
from agents.qualification_agent import qualification_agent
from agents.crm_manager import crm_manager
from agents.nurturing_specialist import nurturing_specialist
from agents.appointment_setter import appointment_setter
from agents.reporting_analytics_agent import reporting_analytics_agent

class Team:
    def __init__(self, name, description, instructions, members):
        self.name = name
        self.description = description
        self.instructions = instructions
        self.members = members

lead_management_team = Team(
    name="Lead Management",
    description="The Lead Management team orchestrates the end-to-end lead lifecycle in the Finance OS, from multi-channel capture and qualification to nurturing, appointment setting, and analytics-driven optimization. Agents collaborate sequentially (e.g., Lead Generator → Qualification Agent → CRM Manager) or in parallel (e.g., Nurturing Specialist running alongside CRM Manager), ensuring seamless data flow and handoffs to convert leads into financial clients efficiently.",
    instructions="""
- Operate as a coordinated unit: Agents share a common database for lead data, with handoffs triggered by status updates (e.g., qualified leads move from Agent 2 to Agent 3).
- Manage handoffs: Use automated triggers (e.g., via CRM Sync Tool) to pass leads; resolve conflicts by prioritizing based on lead score or engagement.
- Handle errors: If an agent fails (e.g., data sync issue), escalate to the Reporting & Analytics Agent for logging and retry; ensure compliance checks at every step.
- Optimize performance: Regularly review KPIs from Agent 6 to refine agent instructions and tool usage.
""",
    members=[
        lead_generator,
        qualification_agent,
        crm_manager,
        nurturing_specialist,
        appointment_setter,
        reporting_analytics_agent,
    ],
)
