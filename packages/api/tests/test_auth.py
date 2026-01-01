"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


class TestAuthRegister:
    """Tests for POST /auth/register."""

    async def test_register_success(self, client: AsyncClient, sample_user_data: dict):
        """Test successful user registration."""
        response = await client.post("/api/v1/auth/register", json=sample_user_data)

        assert response.status_code == 201
        data = response.json()

        # Check user data
        assert data["user"]["email"] == sample_user_data["email"]
        assert data["user"]["display_name"] == sample_user_data["display_name"]
        assert "id" in data["user"]

        # Check tokens
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
        assert data["tokens"]["token_type"] == "bearer"

    async def test_register_duplicate_email(self, client: AsyncClient, sample_user_data: dict):
        """Test registration with duplicate email fails."""
        # First registration
        response = await client.post("/api/v1/auth/register", json=sample_user_data)
        assert response.status_code == 201

        # Duplicate registration
        response = await client.post("/api/v1/auth/register", json=sample_user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with short password fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "short",  # Less than 8 chars
            },
        )
        assert response.status_code == 422  # Validation error

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "validpassword123",
            },
        )
        assert response.status_code == 422


class TestAuthLogin:
    """Tests for POST /auth/login."""

    async def test_login_success(self, client: AsyncClient, sample_user_data: dict):
        """Test successful login."""
        # First register
        await client.post("/api/v1/auth/register", json=sample_user_data)

        # Then login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]

    async def test_login_wrong_password(self, client: AsyncClient, sample_user_data: dict):
        """Test login with wrong password fails."""
        await client.post("/api/v1/auth/register", json=sample_user_data)

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user fails."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 401


class TestAuthRefresh:
    """Tests for POST /auth/refresh."""

    async def test_refresh_success(self, client: AsyncClient, sample_user_data: dict):
        """Test successful token refresh."""
        # Register to get tokens
        register_response = await client.post("/api/v1/auth/register", json=sample_user_data)
        refresh_token = register_response.json()["tokens"]["refresh_token"]

        # Refresh
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token fails."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 401


class TestAuthMe:
    """Tests for GET /auth/me."""

    async def test_get_me_authenticated(
        self, authenticated_client: tuple[AsyncClient, dict]
    ):
        """Test getting current user when authenticated."""
        client, user = authenticated_client

        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user["email"]
        assert data["id"] == user["id"]

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        """Test getting current user when not authenticated fails."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401
