"""Run the recorded contest example in a disposable, localhost-only environment.

conda run --no-capture-output -n rovia python scripts/contest_demo.py
This loads synthetic data; it does not simulate a successful live AI response.
"""

import asyncio
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
API_PORT, WEB_PORT = 8766, 5175


async def seed():
    from sqlalchemy import select
    from app.db import SessionLocal, TripRow, UserRow, VehicleRow, create_tables, engine
    from app.domain.models import Trip, VehicleProfile, utc_now
    from app.services.auth import ensure_configured_admin

    await create_tables()
    await ensure_configured_admin()
    async with SessionLocal() as session:
        user = await session.scalar(select(UserRow).where(UserRow.email == "demo@example.test"))
        trip = Trip.model_validate_json((ROOT / "shared/examples/wuhan-lushan-trip.json").read_text())
        trip.id = "trip_contest_example"
        trip.user_id = user.id
        trip.title = "【示例】武汉·庐山两天一夜"
        vehicle = VehicleProfile(id="vehicle_demo_ev", brand="Rovia", series="演示纯电 SUV",
            model="Rovia 演示车辆", power_type="electric", rated_range_km=560,
            current_energy_percent=80, battery_kwh=82, consumption_per_100km=18,
            max_charge_kw=180, seats=5, has_etc=True)
        now = utc_now()
        session.add(VehicleRow(id=vehicle.id, user_id=user.id, brand=vehicle.brand,
            series=vehicle.series, model=vehicle.model, power_type=vehicle.power_type,
            document=vehicle.model_dump_json(), created_at=now, updated_at=now))
        markdown = [f"# {trip.title}", "", "> 内置合成示例，用于展示操作流程；非实时 AI 生成，不可作为实际出行依据。", ""]
        for day in trip.days:
            markdown.extend([f"## 第 {day.day_index} 天：{day.title}", ""])
            for activity in day.activities:
                markdown.append(f"- {activity.place.name}")
            markdown.append("")
        state = {"status": "completed", "trip_request": trip.request.model_dump(mode="json"),
            "raw_input": trip.request.raw_text, "progress": {"node": "persist_trip", "value": 100},
            "day_plans": [d.model_dump(mode="json") for d in trip.days],
            "verification_issues": [], "tourism_candidates": {}}
        session.add(TripRow(id=trip.id, user_id=user.id, title=trip.title, status="completed",
            document=trip.model_dump_json(), state_json=json.dumps(state, ensure_ascii=False),
            plan_markdown="\n".join(markdown), created_at=now, updated_at=now))
        await session.commit()
    await engine.dispose()


def main():
    if not os.environ.get("CONDA_PREFIX"):
        raise SystemExit("Use the rovia Conda environment.")
    for port in (API_PORT, WEB_PORT):
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                raise SystemExit(f"Port {port} is occupied. Stop that process before starting this demo.")
    children = []
    with tempfile.TemporaryDirectory(prefix="rovia-contest-") as directory:
        os.environ.update({"PYTHONPATH": str(ROOT / "backend"),
            "DATABASE_URL": f"sqlite+aiosqlite:///{directory}/demo.sqlite3",
            "UPLOAD_DIR": f"{directory}/uploads", "ADMIN_EMAIL": "demo@example.test",
            "ADMIN_PASSWORD": "local-contest-demo-only", "ADMIN_DISPLAY_NAME": "演示旅行者",
            "ENABLE_JOB_QUEUE": "false", "LOAD_LOCAL_SKILL_CREDENTIALS": "false",
            "AUTH_COOKIE_SECURE": "false", "CORS_ORIGINS": f"http://127.0.0.1:{WEB_PORT}",
            "ROVIA_API_TARGET": f"http://127.0.0.1:{API_PORT}", "VITE_API_BASE_URL": "",
            "VITE_AMAP_JSAPI_KEY": "", "VITE_AMAP_SECURITY_JS_CODE": ""})
        for key in ("LLM_API_KEY", "OLLAMA_API_KEY", "DEEPSEEK_API_KEY", "AMAP_WEBSERVICE_KEY",
                    "FLYAI_API_KEY", "OPENTRIPMAP_API_KEY", "FLIGHT_FALLBACK_API_KEY",
                    "AVIATIONSTACK_API_KEY", "OIL_APP_ID", "OIL_APP_SECRET"):
            os.environ[key] = ""
        sys.path.insert(0, str(ROOT / "backend"))
        asyncio.run(seed())

        def stop(*_):
            raise KeyboardInterrupt

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        try:
            children.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app",
                "--host", "127.0.0.1", "--port", str(API_PORT)], cwd=ROOT))
            children.append(subprocess.Popen(["npm", "run", "dev", "--", "--host", "127.0.0.1",
                "--port", str(WEB_PORT), "--strictPort"], cwd=ROOT / "frontend"))
            print(f"DEMO: http://127.0.0.1:{WEB_PORT}\nAccount: demo@example.test\nPassword: local-contest-demo-only", flush=True)
            children[0].wait()
        except KeyboardInterrupt:
            pass
        finally:
            for child in children:
                if child.poll() is None:
                    child.terminate()
            for child in children:
                try:
                    child.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()


if __name__ == "__main__":
    main()
