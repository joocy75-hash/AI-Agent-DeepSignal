"""
Integration tests for health check endpoints (Phase 5).
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.api
class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check_basic(self, async_client: AsyncClient):
        """Test basic health check endpoint."""
        response = await async_client.get("/health")

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "uptime_seconds" in data
        assert "uptime_human" in data
        assert "version" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert isinstance(data["uptime_human"], str)

    @pytest.mark.asyncio
    async def test_health_check_db(self, async_client: AsyncClient):
        """Test database health check endpoint."""
        response = await async_client.get("/health/db")

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "response_time_ms" in data
        assert isinstance(data["response_time_ms"], (int, float))
        assert data["response_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_health_check_ready(self, async_client: AsyncClient):
        """Test readiness probe endpoint (Kubernetes)."""
        response = await async_client.get("/health/ready")

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data
        assert "database" in data["checks"]

    @pytest.mark.asyncio
    async def test_health_check_live(self, async_client: AsyncClient):
        """Test liveness probe endpoint (Kubernetes)."""
        response = await async_client.get("/health/live")

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data


@pytest.mark.integration
@pytest.mark.api
class TestHealthEndpointPerformance:
    """Performance tests for health endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint_responds_quickly(self, async_client: AsyncClient):
        """Test that health endpoint responds within acceptable time."""
        import time

        start = time.time()
        response = await async_client.get("/health")
        duration = time.time() - start

        assert response.status_code == 200
        # Health check should respond in less than 100ms
        assert duration < 0.1

    @pytest.mark.asyncio
    async def test_db_health_check_responds_quickly(self, async_client: AsyncClient):
        """Test that DB health check responds within acceptable time."""
        import time

        start = time.time()
        response = await async_client.get("/health/db")
        duration = time.time() - start

        assert response.status_code == 200
        # DB health check should respond in less than 500ms
        assert duration < 0.5

        # Verify reported response time is reasonable
        data = response.json()
        assert data["response_time_ms"] < 500
