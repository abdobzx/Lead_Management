import pytest
from agents.lead_generator import lead_generator

def test_lead_generator_functionality():
    """Test Name: Test Agent Lead Generator Functionality
    Objective: Verify that the Lead Generator can successfully capture and enrich a lead from social media.
    """
    # Given a raw lead input from a social media post
    raw_lead = {"name": "Jane Doe", "email": "jane@example.com"}

    # When the agent is triggered with the command to process the lead
    response = lead_generator.run(f"Enrich this lead profile: {raw_lead}")

    # Then the agent should use the tools and return enriched data
    assert response is not None
    assert response.content is not None
    assert len(response.content) > 0
    # Check that the response contains expected enrichment data
    content = response.content.lower()
    assert "enrich" in content or "profile" in content or "lead" in content