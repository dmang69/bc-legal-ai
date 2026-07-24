"""End-to-end tests hitting a real Postgres via TestClient.

Run against a live Postgres:
    DATABASE_URL=postgresql+psycopg://... pytest tests/

The docker-compose 'test' service (or your local Postgres) must be running.
"""
from __future__ import annotations

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


@pytest.fixture(scope="session")
def client():
    from app.main import app
    from app.db import get_engine

    # Ensure schema is up
    from alembic.config import Config
    from alembic import command

    cfg = Config("alembic.ini")
    cfg.set_main_option("script_location", "alembic")
    command.upgrade(cfg, "head")

    with TestClient(app) as c:
        yield c


@pytest.fixture
def clean_db():
    """Truncate everything between tests, then re-seed defaults."""
    from app.db import get_engine
    from app.main import seed_default_prompts
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE audits, settings, prompts, files, messages, chats, "
            "workspaces, sessions, users RESTART IDENTITY CASCADE"
        ))
    seed_default_prompts()
    yield


def _unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:8]}@example.com"


def test_health_is_public(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_unauth_bootstrap_is_401(client, clean_db):
    r = client.get("/api/bootstrap")
    assert r.status_code == 401


def test_register_login_bootstrap_flow(client, clean_db):
    email = _unique_email()
    r = client.post("/api/auth/register", json={
        "email": email,
        "password": "HorseBattery123!",
        "display_name": "Dan",
    })
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["role"] == "admin", "first user must become admin"

    r = client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == email

    r = client.get("/api/bootstrap")
    assert r.status_code == 200
    boot = r.json()
    assert boot["user"]["role"] == "admin"
    assert isinstance(boot["models"], list) and len(boot["models"]) >= 1
    assert boot["prompts"], "default shared prompts should be seeded"


def test_second_registration_blocked(client, clean_db):
    # first user
    r = client.post("/api/auth/register", json={
        "email": _unique_email(), "password": "HorseBattery123!", "display_name": "One",
    })
    assert r.status_code == 201

    # log out so cookie isn't sent
    client.post("/api/auth/logout")

    r = client.post("/api/auth/register", json={
        "email": _unique_email(), "password": "HorseBattery123!", "display_name": "Two",
    })
    assert r.status_code == 403


def test_weak_password_rejected(client, clean_db):
    r = client.post("/api/auth/register", json={
        "email": _unique_email(), "password": "short", "display_name": "Weak",
    })
    # Pydantic min_length rejects at 422; if it slips past (matches min), our
    # strength check returns 400. Either is acceptable.
    assert r.status_code in (400, 422)


def test_wrong_password_401(client, clean_db):
    email = _unique_email()
    client.post("/api/auth/register", json={
        "email": email, "password": "HorseBattery123!", "display_name": "Dan",
    })
    client.post("/api/auth/logout")
    r = client.post("/api/auth/login", json={"email": email, "password": "WrongOne1234!"})
    assert r.status_code == 401


def test_workspace_ownership_isolation(client, clean_db):
    # user A creates a workspace
    email_a = _unique_email()
    client.post("/api/auth/register", json={
        "email": email_a, "password": "HorseBattery123!", "display_name": "A",
    })
    ws = client.post("/api/workspaces", json={"name": "A-ws", "kind": "general"}).json()
    assert ws["id"]

    # log out user A
    client.post("/api/auth/logout")

    # register user B via bootstrap-token env (would need to be set); skip
    # cross-user test here for lack of that plumbing in this tier.
    # Instead, verify unauth cannot see A's data
    r = client.get(f"/api/chats?workspace_id={ws['id']}")
    assert r.status_code == 401


def test_admin_health_requires_admin(client, clean_db):
    email = _unique_email()
    client.post("/api/auth/register", json={
        "email": email, "password": "HorseBattery123!", "display_name": "Admin",
    })
    r = client.get("/api/admin/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "users" in body["counts"]


def test_logout_revokes_session(client, clean_db):
    client.post("/api/auth/register", json={
        "email": _unique_email(), "password": "HorseBattery123!", "display_name": "Dan",
    })
    r = client.post("/api/auth/logout")
    assert r.status_code == 204
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_full_chat_flow(client, clean_db):
    client.post("/api/auth/register", json={
        "email": _unique_email(), "password": "HorseBattery123!", "display_name": "Dan",
    })
    ws = client.post("/api/workspaces", json={"name": "W1", "kind": "general"}).json()
    chat = client.post("/api/chats", json={"workspace_id": ws["id"], "title": "Test"}).json()

    r = client.post(
        f"/api/chats/{chat['id']}/messages",
        json={"content": "Hello", "mode": "general", "model_id": "mock-general"},
    )
    assert r.status_code == 200
    assert "reply" in r.json()

    r = client.get(f"/api/chats/{chat['id']}")
    assert r.status_code == 200
    body = r.json()
    assert len(body["messages"]) == 2
    assert body["messages"][0]["role"] == "user"
    assert body["messages"][1]["role"] == "assistant"
