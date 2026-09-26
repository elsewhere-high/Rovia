"""Start Rovia locally: conda run --no-capture-output -n rovia python scripts/dev.py."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
from urllib.parse import urlparse
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
children: list[subprocess.Popen] = []
stopping = False


def stop(*_args) -> None:
    global stopping
    stopping = True


def port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.3):
            return True
    except OSError:
        return False


def start(command: list[str], *, cwd: Path = ROOT) -> subprocess.Popen:
    child = subprocess.Popen(command, cwd=cwd, env=os.environ.copy(), start_new_session=True)
    children.append(child)
    return child


def main() -> int:
    if not os.environ.get("CONDA_PREFIX"):
        raise RuntimeError("请使用 conda run --no-capture-output -n rovia python scripts/dev.py")
    if not (ROOT / ".env").exists():
        shutil.copyfile(ROOT / ".env.example", ROOT / ".env")
    os.chdir(ROOT)
    os.environ["PYTHONPATH"] = str(ROOT / "backend")
    os.environ["PYTHONUNBUFFERED"] = "1"
    sys.path.insert(0, str(ROOT / "backend"))
    from app.core.config import get_settings

    settings = get_settings()
    api_port = int(os.environ.get("ROVIA_API_PORT", "8000"))
    web_port = int(os.environ.get("ROVIA_WEB_PORT", "5373"))
    for port in (api_port, web_port):
        if port_open("127.0.0.1", port):
            raise RuntimeError(f"本地端口 {port} 已被占用，请先停止占用该端口的服务。")
    if not (ROOT / "frontend/node_modules").is_dir():
        raise RuntimeError("请先在 frontend 目录使用 Conda 环境运行 npm ci。")
    redis_url = urlparse(settings.redis_url)
    redis_host = redis_url.hostname or "127.0.0.1"
    redis_port = redis_url.port or 6379
    if redis_host in {"localhost", "127.0.0.1"} and not port_open(redis_host, redis_port):
        executable = shutil.which("redis-server")
        if not executable:
            raise RuntimeError("缺少 redis-server，请更新 environment.yml 对应的 Conda 环境。")
        if redis_url.password:
            raise RuntimeError("配置含 Redis 密码，请先自行启动对应 Redis 实例。")
        redis_data = ROOT / "data/redis"
        redis_data.mkdir(parents=True, exist_ok=True)
        start([executable, "--bind", "127.0.0.1", "--port", str(redis_port),
               "--dir", str(redis_data), "--appendonly", "yes"])
    from redis import Redis

    redis_client = Redis.from_url(settings.redis_url, socket_connect_timeout=1)
    for attempt in range(30):
        try:
            redis_client.ping()
            break
        except Exception:
            if attempt == 29:
                raise RuntimeError("Redis 未就绪，请检查 REDIS_URL 与服务状态。") from None
            time.sleep(0.2)
    redis_client.close()
    subprocess.run([sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"], check=True)
    api = start([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(api_port)])
    for _ in range(100):
        if api.poll() is not None:
            raise RuntimeError("Rovia API 启动失败。")
        try:
            with urlopen(f"http://127.0.0.1:{api_port}/health", timeout=1) as response:
                if response.status == 200:
                    break
        except OSError:
            time.sleep(0.2)
    else:
        raise RuntimeError("Rovia API 就绪等待超时。")
    if settings.enable_job_queue:
        start([sys.executable, "-m", "arq", "app.workers.main.WorkerSettings"])
    os.environ["ROVIA_API_TARGET"] = f"http://127.0.0.1:{api_port}"
    start(["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", str(web_port), "--strictPort"], cwd=ROOT / "frontend")
    print(f"\nRovia → http://127.0.0.1:{web_port}  |  API → http://127.0.0.1:{api_port}/docs\n按 Ctrl+C 停止本次启动的服务。\n", flush=True)
    while not stopping:
        for child in children:
            if child.poll() is not None:
                raise RuntimeError(f"Rovia 子进程退出，状态码 {child.returncode}。")
        time.sleep(0.3)
    return 0


if __name__ == "__main__":
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        code = main()
    except Exception as error:
        print(f"Rovia: {error}", file=sys.stderr)
        code = 1
    finally:
        for child in reversed(children):
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
        for child in children:
            try:
                child.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
    raise SystemExit(code)
