import pytest
from fastapi import status


@pytest.mark.unit
class TestHealth:
    """test health check endpoints"""
    
    def test_basic_health_check(self, client):
        """test basic health endpoint"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
    
    def test_detailed_health_check(self, client):
        """test detailed health check with dependencies"""
        response = client.get("/health/detailed")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "dependencies" in data
        assert "database" in data["dependencies"]
        assert "redis" in data["dependencies"]
