"""
Tests for authentication endpoints.
"""
import pytest
from fastapi import status


def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepassword123"
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["is_active"] is True
    assert "api_key" in data


def test_register_duplicate_email(client, test_user):
    """Test registration with duplicate email fails."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,
            "password": "password123"
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in response.json()["detail"]


def test_login(client, test_user):
    """Test user login."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    """Test login with wrong password fails."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "wrongpassword"
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user(client, test_user, auth_headers):
    """Test getting current user info."""
    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == test_user.id


def test_regenerate_api_key(client, test_user, auth_headers):
    """Test API key regeneration."""
    old_api_key = test_user.api_key

    response = client.post(
        "/api/v1/auth/api-key/regenerate",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "api_key" in data
    assert data["api_key"] != old_api_key
