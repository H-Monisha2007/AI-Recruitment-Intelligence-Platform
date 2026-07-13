"""
Integration tests — Auth API endpoints.
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ── Register ──────────────────────────────────────────────────────────────────

async def test_register_success(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "password": "Strong1234",
        "full_name": "New User",
        "role": "candidate",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["role"] == "candidate"
    assert "hashed_password" not in data


async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "Strong1234", "full_name": "Dup", "role": "candidate"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400


async def test_register_weak_password(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "weak@example.com",
        "password": "short",
        "full_name": "Weak",
        "role": "candidate",
    })
    assert resp.status_code == 422


async def test_register_invalid_role(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "bad@example.com",
        "password": "Strong1234",
        "full_name": "Bad Role",
        "role": "superuser",  # invalid
    })
    assert resp.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

async def test_login_success(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com", "password": "Login1234", "full_name": "Login", "role": "candidate"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com", "password": "Login1234"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "wrongpw@example.com", "password": "Correct1234", "full_name": "WP", "role": "candidate"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "wrongpw@example.com", "password": "WrongPassword"
    })
    assert resp.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com", "password": "Anything1"
    })
    assert resp.status_code == 401


# ── /me ───────────────────────────────────────────────────────────────────────

async def test_me_authenticated(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert "email" in resp.json()


async def test_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_invalid_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer badtoken.abc.xyz"})
    assert resp.status_code == 401
