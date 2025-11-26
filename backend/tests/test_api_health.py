"""
Tests for health check and basic API endpoints.
"""
from fastapi import status


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data


def test_docs_endpoint(client):
    """Test that API documentation is accessible."""
    response = client.get("/docs")

    assert response.status_code == status.HTTP_200_OK
