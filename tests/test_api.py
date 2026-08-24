"""
Tests for the Lead Management API endpoints - now against the real leads
table and real auth (see app/models/db_models.py, app/api/v1/endpoints/auth.py),
not the shared, unauthenticated in-memory dict this used to test.
"""

import uuid

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Test client fixture. Uses `with` so the FastAPI lifespan actually
    runs create_tables() - without it, the in-memory SQLite test DB never
    gets its schema and every query fails with "no such table"."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client():
    """Async test client fixture."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


def _register_and_login(client: TestClient) -> dict:
    """Registers a fresh, uniquely-emailed user and returns Bearer auth
    headers. Unique per call because the test DB (SQLite StaticPool) is
    shared across all tests in a session, so a fixed email would collide."""
    email = f"test-{uuid.uuid4().hex[:12]}@example.com"
    password = "supersecret123"
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    r = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers(client):
    return _register_and_login(client)


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


class TestAuth:
    """Test registration/login - previously nonexistent, endpoints didn't exist."""

    def test_register_and_login(self, client):
        headers = _register_and_login(client)
        assert "Authorization" in headers

    def test_duplicate_registration_rejected(self, client):
        email = f"test-{uuid.uuid4().hex[:12]}@example.com"
        r = client.post("/api/v1/auth/register", json={"email": email, "password": "supersecret123"})
        assert r.status_code == 200
        r = client.post("/api/v1/auth/register", json={"email": email, "password": "supersecret123"})
        assert r.status_code == 400

    def test_login_wrong_password_rejected(self, client):
        email = f"test-{uuid.uuid4().hex[:12]}@example.com"
        client.post("/api/v1/auth/register", json={"email": email, "password": "supersecret123"})
        r = client.post("/api/v1/auth/login", data={"username": email, "password": "wrongpassword"})
        assert r.status_code == 401


class TestLeadsAPI:
    """Test leads management endpoints - each lead is owned by an
    authenticated user; unauthenticated access is rejected."""

    def test_unauthenticated_create_rejected(self, client):
        response = client.post("/api/v1/leads/", json={"name": "X", "email": "x@example.com"})
        assert response.status_code == 401

    def test_create_lead(self, client, auth_headers):
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

        response = client.post("/api/v1/leads/", json=lead_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == lead_data["name"]
        assert data["email"] == lead_data["email"]
        assert "id" in data
        assert data["status"] == "new"

    def test_get_leads(self, client, auth_headers):
        """Test getting all leads for the current user."""
        response = client.get("/api/v1/leads/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        assert "total" in data
        assert isinstance(data["leads"], list)

    def test_get_lead_by_id(self, client, auth_headers):
        """Test getting a specific lead."""
        lead_data = {
            "name": "Test User 2",
            "email": "test2@example.com"
        }
        create_response = client.post("/api/v1/leads/", json=lead_data, headers=auth_headers)
        lead_id = create_response.json()["id"]

        response = client.get(f"/api/v1/leads/{lead_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == lead_id
        assert data["name"] == lead_data["name"]

    def test_get_lead_by_id_wrong_owner_rejected(self, client, auth_headers):
        """A different user cannot fetch someone else's lead by id."""
        create_response = client.post(
            "/api/v1/leads/", json={"name": "Owned", "email": "owned@example.com"}, headers=auth_headers
        )
        lead_id = create_response.json()["id"]

        other_user_headers = _register_and_login(client)
        response = client.get(f"/api/v1/leads/{lead_id}", headers=other_user_headers)
        assert response.status_code == 404

    def test_update_lead(self, client, auth_headers):
        """Test updating a lead."""
        lead_data = {
            "name": "Test User 3",
            "email": "test3@example.com"
        }
        create_response = client.post("/api/v1/leads/", json=lead_data, headers=auth_headers)
        lead_id = create_response.json()["id"]

        update_data = {
            "name": "Updated Test User",
            "status": "qualified"
        }
        response = client.put(f"/api/v1/leads/{lead_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["status"] == update_data["status"]

    def test_delete_lead(self, client, auth_headers):
        """Test deleting a lead."""
        lead_data = {
            "name": "Test User 4",
            "email": "test4@example.com"
        }
        create_response = client.post("/api/v1/leads/", json=lead_data, headers=auth_headers)
        lead_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/leads/{lead_id}", headers=auth_headers)
        assert response.status_code == 200

        get_response = client.get(f"/api/v1/leads/{lead_id}", headers=auth_headers)
        assert get_response.status_code == 404


class TestAnalyticsAPI:
    """Test analytics endpoints - scoped to the current authenticated user."""

    def test_get_lead_analytics(self, client, auth_headers):
        """Test getting lead analytics."""
        response = client.get("/api/v1/analytics/leads", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_leads" in data
        assert "qualified_leads" in data
        assert "conversion_rate" in data

    def test_get_agent_analytics(self, client, auth_headers):
        """Test getting agent performance analytics."""
        response = client.get("/api/v1/analytics/agents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_get_dashboard_data(self, client, auth_headers):
        """Test getting dashboard overview data - computed from the real
        leads table and real pipeline stats, not the fake
        recent_activity/performance_trends this used to assert on."""
        response = client.get("/api/v1/analytics/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "total_leads" in data["summary"]
        assert "agent_pipeline_stats" in data


class TestLeadProcessing:
    """Test lead processing with AI agents - runs the real 6-agent
    pipeline against the live API, so this makes real API calls and
    takes roughly a minute."""

    def test_process_lead(self, client, auth_headers):
        """Test processing a lead through the real AI agent pipeline."""
        lead_data = {
            "name": "Process Test User",
            "email": "process@example.com",
            "budget": 75000
        }
        create_response = client.post("/api/v1/leads/", json=lead_data, headers=auth_headers)
        lead_id = create_response.json()["id"]

        response = client.post(f"/api/v1/leads/{lead_id}/process", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["lead_id"] == lead_id
        assert data["succeeded"] is True
        assert data["status"] in {"new", "qualified", "nurturing", "appointment_set", "converted", "lost"}
        assert len(data["stages"]) == 6
        assert all(stage["error"] is None for stage in data["stages"])

        # Score extraction is best-effort (see _extract_score in leads.py):
        # it matches key names the LLM used in this particular run, which
        # aren't perfectly deterministic. Assert it's either a valid 0-100
        # score or None - not "always populated", which the design doesn't
        # actually guarantee.
        lead_response = client.get(f"/api/v1/leads/{lead_id}", headers=auth_headers)
        score = lead_response.json()["score"]
        assert score is None or 0 <= score <= 100
