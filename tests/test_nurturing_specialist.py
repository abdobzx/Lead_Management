import pytest
from agents.nurturing_specialist import nurturing_specialist

def test_nurturing_specialist_functionality():
    """Test Name: Test Agent Nurturing Specialist Functionality
    Objective: Verify that the Nurturing Specialist can successfully create and send a personalized market insight campaign.
    """
    # Given a lead segment with interests in stock market trends
    segment = "stock market"

    # When the agent is triggered with the command to nurture the segment
    response = nurturing_specialist.run(f"Create nurturing content for segment: {segment}")

    # Then the agent should use the tools and return content data
    assert response is not None
    assert response.content is not None
    assert len(response.content) > 0
    # Check that the response contains expected content data
    content = response.content.lower()
    assert "content" in content or "campaign" in content or "nurture" in content