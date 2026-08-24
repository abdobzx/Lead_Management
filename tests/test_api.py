"""
Tests for the Lead Management API endpoints.
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async test client fixture."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


class TestHealthCheck:
    """Test health check endpoints."""

    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_detailed_health_check(self, client):
        """Test detailed health check."""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "timestamp" in data


class TestLeadsAPI:
    """Test leads management endpoints."""

    def test_create_lead(self, client):
        """Test creating a new lead."""
        lead_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+1234567890",
            "company": "Test Corp",
            "source": "website",
            "budget": 50000,
            "timeline": "3 months"
        }

        response = client.post("/api/v1/leads/", json=lead_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == lead_data["name"]
        assert data["email"] == lead_data["email"]
        assert "id" in data
        assert data["status"] == "new"

    def test_get_leads(self, client):
        """Test getting all leads."""
        response = client.get("/api/v1/leads/")
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        assert "total" in data
        assert isinstance(data["leads"], list)

    def test_get_lead_by_id(self, client):
        """Test getting a specific lead."""
        # First create a lead
        lead_data = {
            "name": "Test User 2",
            "email": "test2@example.com"
        }
        create_response = client.post("/api/v1/leads/", json=lead_data)
        lead_id = create_response.json()["id"]

        # Then get it
        response = client.get(f"/api/v1/leads/{lead_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == lead_id
        assert data["name"] == lead_data["name"]

    def test_update_lead(self, client):
        """Test updating a lead."""
        # Create a lead
        lead_data = {
            "name": "Test User 3",
            "email": "test3@example.com"
        }
        create_response = client.post("/api/v1/leads/", json=lead_data)
        lead_id = create_response.json()["id"]

        # Update it
        update_data = {
            "name": "Updated Test User",
            "status": "qualified"
        }
        response = client.put(f"/api/v1/leads/{lead_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["status"] == update_data["status"]

    def test_delete_lead(self, client):
        """Test deleting a lead."""
        # Create a lead
        lead_data = {
            "name": "Test User 4",
            "email": "test4@example.com"
        }
        create_response = client.post("/api/v1/leads/", json=lead_data)
        lead_id = create_response.json()["id"]

        # Delete it
        response = client.delete(f"/api/v1/leads/{lead_id}")
        assert response.status_code == 200

        # Verify it's gone
        get_response = client.get(f"/api/v1/leads/{lead_id}")
        assert get_response.status_code == 404


class TestAnalyticsAPI:
    """Test analytics endpoints."""

    def test_get_lead_analytics(self, client):
        """Test getting lead analytics."""
        response = client.get("/api/v1/analytics/leads")
        assert response.status_code == 200
        data = response.json()
        assert "total_leads" in data
        assert "qualified_leads" in data
        assert "conversion_rate" in data

    def test_get_agent_analytics(self, client):
        """Test getting agent performance analytics."""
        response = client.get("/api/v1/analytics/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # Should have agent data
        assert len(data) > 0

    def test_get_dashboard_data(self, client):
        """Test getting dashboard overview data - computed from real
        in-memory leads_db and real pipeline stats, not the fake
        recent_activity/performance_trends this used to assert on."""
        response = client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "total_leads" in data["summary"]
        assert "agent_pipeline_stats" in data


class TestLeadProcessing:
    """Test lead processing with AI agents - runs the real 6-agent
    pipeline against the live API, so this makes real API calls and
    takes roughly a minute."""

    def test_process_lead(self, client):
        """Test processing a lead through the real AI agent pipeline."""
        # Create a lead first
        lead_data = {
            "name": "Process Test User",
            "email": "process@example.com",
            "budget": 75000
        }
        create_response = client.post("/api/v1/leads/", json=lead_data)
        lead_id = create_response.json()["id"]

        response = client.post(f"/api/v1/leads/{lead_id}/process")
        assert response.status_code == 200
        data = response.json()
        assert data["lead_id"] == lead_id
        assert data["succeeded"] is True
        assert data["status"] in {"new", "qualified", "nurturing", "appointment_set", "converted", "lost"}
        assert len(data["stages"]) == 6
        assert all(stage["error"] is None for stage in data["stages"])

        # The lead's score field should be populated from the pipeline's
        # qualification stage.
        lead_response = client.get(f"/api/v1/leads/{lead_id}")
        assert lead_response.json()["score"] is not None