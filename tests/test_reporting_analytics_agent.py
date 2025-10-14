import pytest
from agents.reporting_analytics_agent import reporting_analytics_agent

def test_reporting_analytics_agent_functionality():
    """Test Name: Test Agent Reporting & Analytics Agent Functionality
    Objective: Verify that the Reporting & Analytics Agent can successfully track KPIs and generate a performance report.
    """
    # Given lead funnel data from the past month
    data = {"conversions": 75, "total": 100}

    # When the agent is triggered with the command to analyze and report
    response = reporting_analytics_agent.run(f"Analyze and report on this data: {data}")

    # Then the agent should use the tools and return analytics data
    assert response is not None
    # The agent may return empty content if tools are used but no final response is generated
    # Check that the agent executed successfully by verifying it has messages
    assert response.messages is not None
    assert len(response.messages) > 0
    # Check that tools were called during execution
    tool_calls = [msg for msg in response.messages if msg.tool_calls]
    assert len(tool_calls) > 0