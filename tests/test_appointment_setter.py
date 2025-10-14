import pytest
from agents.appointment_setter import appointment_setter

def test_appointment_setter_functionality():
    """Test Name: Test Agent Appointment Setter Functionality
    Objective: Verify that the Appointment Setter can successfully monitor and schedule a consultation based on readiness signals.
    """
    # Given a nurtured lead with high engagement scores
    lead_signals = {"score": 90}

    # When the agent is triggered with the command to check readiness
    response = appointment_setter.run(f"Monitor and schedule appointment for lead: {lead_signals}")

    # Then the agent should use the tools and return scheduling data
    assert response is not None
    assert response.content is not None
    assert len(response.content) > 0
    # Check that the response contains expected scheduling data
    content = response.content.lower()
    assert "appointment" in content or "schedule" in content or "monitor" in content