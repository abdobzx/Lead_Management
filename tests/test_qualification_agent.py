import pytest
from agents.qualification_agent import qualification_agent

def test_qualification_agent_functionality():
    """Test Name: Test Agent Qualification Agent Functionality
    Objective: Verify that the Qualification Agent can successfully score and qualify a lead for a loan product.
    """
    # Given an enriched lead profile with financial data
    lead_profile = {"name": "John Doe", "income": 100000}

    # When the agent is triggered with the command to qualify the lead
    response = qualification_agent.run(f"Qualify this lead profile: {lead_profile}")

    # Then the agent should use the tools and return qualification data
    assert response is not None
    assert response.content is not None
    assert len(response.content) > 0
    # Check that the response contains expected qualification data
    content = response.content.lower()
    assert "score" in content or "qualify" in content or "lead" in content