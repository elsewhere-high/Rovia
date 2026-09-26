"""Run the browser-test API against disposable data and explicit test credentials."""

import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if not os.environ.get("CONDA_PREFIX"):
    raise SystemExit("Browser tests require the rovia Conda environment.")

with tempfile.TemporaryDirectory(prefix="rovia-browser-tests-") as directory:
    env = os.environ.copy()
    env.update({
        "PYTHONPATH": str(ROOT / "backend"),
        "DATABASE_URL": f"sqlite+aiosqlite:///{directory}/test.sqlite3",
        "UPLOAD_DIR": f"{directory}/uploads",
        "ADMIN_EMAIL": "ui-test@example.test",
        "ADMIN_PASSWORD": "local-browser-test-password",
        "ADMIN_DISPLAY_NAME": "旅行者",
        "ENABLE_JOB_QUEUE": "false",
        "LOAD_LOCAL_SKILL_CREDENTIALS": "false",
        "CORS_ORIGINS": "http://127.0.0.1:5174",
        "AUTH_COOKIE_SECURE": "false",
    })
    for key in ("LLM_API_KEY", "OLLAMA_API_KEY", "DEEPSEEK_API_KEY", "AMAP_WEBSERVICE_KEY",
                "FLYAI_API_KEY", "OPENTRIPMAP_API_KEY", "FLIGHT_FALLBACK_API_KEY",
                "AVIATIONSTACK_API_KEY", "OIL_APP_ID", "OIL_APP_SECRET"):
        env[key] = ""
    child = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8765"], cwd=ROOT, env=env)
    signal.signal(signal.SIGTERM, lambda *_: child.terminate())
    signal.signal(signal.SIGINT, lambda *_: child.terminate())
    try:
        raise SystemExit(child.wait())
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=10)
