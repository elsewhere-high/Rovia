from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db import SessionLocal, SkillCallRow, TripRow
from app.main import app
from app.planning.llm import _audit_llm_call, reset_current_user_id, set_current_user_id
from app.services.auth import migrate_legacy_data


@pytest.mark.asyncio
async def test_business_api_requires_authentication(client):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as anonymous:
        response = await anonymous.post(
            "/api/v1/trips",
            json={"title": "匿名行程", "request": {"raw_text": "武汉周末游"}},
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "AUTH_REQUIRED"

        ops_response = await anonymous.get("/api/v1/ops/metrics")
        assert ops_response.status_code == 401


@pytest.mark.asyncio
async def test_users_are_isolated_and_legacy_rows_can_be_assigned_to_admin(client):
    admin = (await client.get("/api/v1/auth/me")).json()
    email = f"user-{uuid4().hex[:10]}@example.test"
    created_user = await client.post(
        "/api/v1/auth/users",
        json={
            "email": email,
            "password": "user-password-123",
            "display_name": "隔离用户",
        },
    )
    assert created_user.status_code == 201
    assert created_user.json()["role"] == "user"

    admin_trip = await client.post(
        "/api/v1/trips",
        json={"title": "管理员行程", "request": {"raw_text": "管理员数据"}},
    )
    assert admin_trip.status_code == 201
    admin_trip_id = admin_trip.json()["id"]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as other:
        login = await other.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "user-password-123"},
        )
        assert login.status_code == 200
        assert login.json()["id"] == created_user.json()["id"]
        assert (await other.get("/api/v1/auth/users")).status_code == 403

        assert (await other.get(f"/api/v1/trips/{admin_trip_id}")).status_code == 404
        assert all(
            item["id"] != admin_trip_id
            for item in (await other.get("/api/v1/trips")).json()
        )

        user_trip = await other.post(
            "/api/v1/trips",
            json={"title": "普通用户行程", "request": {"raw_text": "用户数据"}},
        )
        assert user_trip.status_code == 201
        user_trip_id = user_trip.json()["id"]

        now = datetime.now(timezone.utc)
        async with SessionLocal() as session:
            session.add(
                SkillCallRow(
                    id=f"skillcall_{uuid4().hex[:12]}",
                    user_id=admin["id"],
                    request_id="auth-isolation-admin",
                    trip_id=admin_trip_id,
                    adapter="test.auth_isolation_admin",
                    provider="test",
                    success=True,
                    cache_hit=False,
                    latency_ms=1,
                    source_summary_json="[]",
                    created_at=now,
                )
            )
            session.add(
                SkillCallRow(
                    id=f"skillcall_{uuid4().hex[:12]}",
                    user_id=created_user.json()["id"],
                    request_id="auth-isolation-user",
                    trip_id=user_trip_id,
                    adapter="test.auth_isolation_user",
                    provider="test",
                    success=True,
                    cache_hit=False,
                    latency_ms=1,
                    source_summary_json="[]",
                    created_at=now,
                )
            )
            await session.commit()
        calls = await other.get("/api/v1/skills/calls")
        assert calls.status_code == 200
        assert all(item["request_id"] != "auth-isolation-admin" for item in calls.json())
        assert any(item["request_id"] == "auth-isolation-user" for item in calls.json())

    assert (await client.get(f"/api/v1/trips/{user_trip_id}")).status_code == 404
    assert all(
        item["id"] != user_trip_id
        for item in (await client.get("/api/v1/trips")).json()
    )

    async with SessionLocal() as session:
        row = await session.scalar(select(TripRow).where(TripRow.id == admin_trip_id))
        assert row is not None
        row.user_id = None
        await session.commit()

    async with SessionLocal() as session:
        migrated = await migrate_legacy_data(session, admin["id"])
        assert migrated >= 1

    async with SessionLocal() as session:
        row = await session.scalar(select(TripRow).where(TripRow.id == admin_trip_id))
        assert row is not None
        assert row.user_id == admin["id"]


@pytest.mark.asyncio
async def test_agent_audit_is_bound_to_current_user(client):
    admin = (await client.get("/api/v1/auth/me")).json()
    token = set_current_user_id(admin["id"])
    try:
        await _audit_llm_call(
            "auth_context",
            provider="test",
            success=True,
            latency_ms=1,
            usage={"total_tokens": 3},
        )
    finally:
        reset_current_user_id(token)

    async with SessionLocal() as session:
        row = await session.scalar(
            select(SkillCallRow).where(SkillCallRow.adapter == "agent.auth_context")
        )
    assert row is not None
    assert row.user_id == admin["id"]
