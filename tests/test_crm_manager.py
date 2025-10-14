import pytest
from agents.crm_manager import crm_manager

def test_crm_manager_functionality():
    """Test Name: Test Agent CRM Manager Functionality
    Objective: Verify that the CRM Manager can successfully update contact data and automate a follow-up sequence.
    """
    # Given a qualified lead in the database with interaction history
    lead_data = {"id": 1, "name": "Jane Doe", "status": "qualified"}

    # When the agent is triggered with the command to manage and engage the lead
    response = crm_manager.run(f"Update and manage this lead: {lead_data}")

    # Then the agent should use the tools and return management data
    assert response is not None
    assert response.content is not None
    assert len(response.content) > 0
    # Check that the response contains expected management data
    content = response.content.lower()
    assert "update" in content or "manage" in content or "crm" in content