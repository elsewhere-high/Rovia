import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["LOAD_LOCAL_SKILL_CREDENTIALS"] = "false"
os.environ["ENABLE_JOB_QUEUE"] = "false"
# Tests must never consume a developer's real provider credentials from the
# ignored .env file.  Provider-degradation assertions are intentionally
# deterministic; integration calls are exercised separately in Docker.
for _provider_key in (
    "LLM_API_KEY",
    "AMAP_WEBSERVICE_KEY",
    "OPENTRIPMAP_API_KEY",
    "FLYAI_API_KEY",
    "OLLAMA_API_KEY",
    "DEEPSEEK_API_KEY",
):
    os.environ[_provider_key] = ""
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="rovia-test-uploads-")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db import create_tables
from app.main import app

TEST_ADMIN = {
    "email": "test-admin@example.test",
    "password": "test-admin-password",
    "display_name": "测试管理员",
}


@pytest_asyncio.fixture
async def client():
    await create_tables()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as value:
        status = await value.get("/api/v1/auth/status")
        assert status.status_code == 200
        if status.json()["setup_required"]:
            initialized = await value.post("/api/v1/auth/setup", json=TEST_ADMIN)
            assert initialized.status_code == 201, initialized.text
        else:
            authenticated = await value.post(
                "/api/v1/auth/login",
                json={"email": TEST_ADMIN["email"], "password": TEST_ADMIN["password"]},
            )
            assert authenticated.status_code == 200, authenticated.text
        yield value
