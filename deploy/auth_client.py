"""Authenticate live acceptance clients without exposing credentials."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests


class AuthenticationError(RuntimeError):
    """Raised when a live acceptance client cannot establish a session."""


def _configured_value(name: str) -> str:
    value = os.getenv(name)
    if value is not None:
        return value
    dotenv = Path(__file__).resolve().parents[1] / ".env"
    try:
        lines = dotenv.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, raw_value = stripped.split("=", 1)
        if key.strip() != name:
            continue
        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        return value
    return ""


def _credential(primary: str, fallback: str, *, trim: bool = False) -> str:
    value = _configured_value(primary) or _configured_value(fallback)
    return value.strip() if trim else value


def _response_code(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return f"HTTP_{response.status_code}"
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and error.get("code"):
            return str(error["code"])
    return f"HTTP_{response.status_code}"


def authenticate_session(
    session: requests.Session,
    base_url: str,
    *,
    require_role: str | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """Log in the supplied session, initializing the first admin if needed.

    Credentials are read from ``ROVIA_SMOKE_EMAIL``/``PASSWORD`` first and
    then ``ADMIN_EMAIL``/``PASSWORD``. They are never included in exceptions.
    """
    base = base_url.rstrip("/")
    try:
        status = session.get(f"{base}/api/v1/auth/status", timeout=timeout)
    except requests.RequestException as error:
        raise AuthenticationError(f"auth status request failed: {error}") from error
    if status.status_code != 200:
        raise AuthenticationError(f"auth status failed: {_response_code(status)}")
    try:
        status_payload = status.json()
    except ValueError as error:
        raise AuthenticationError("auth status returned invalid JSON") from error

    if not isinstance(status_payload, dict):
        raise AuthenticationError("auth status returned an invalid payload")
    email = _credential("ROVIA_SMOKE_EMAIL", "ADMIN_EMAIL", trim=True)
    password = _credential("ROVIA_SMOKE_PASSWORD", "ADMIN_PASSWORD")
    if not email or not password:
        raise AuthenticationError(
            "set ROVIA_SMOKE_EMAIL and ROVIA_SMOKE_PASSWORD "
            "(or ADMIN_EMAIL and ADMIN_PASSWORD) before running live acceptance"
        )

    setup_required = bool(status_payload.get("setup_required"))
    if setup_required:
        endpoint = "/api/v1/auth/setup"
        body = {
            "email": email,
            "password": password,
            "display_name": (
                _configured_value("ROVIA_SMOKE_DISPLAY_NAME")
                or _configured_value("ADMIN_DISPLAY_NAME")
                or "Acceptance Admin"
            ).strip(),
        }
    else:
        endpoint = "/api/v1/auth/login"
        body = {"email": email, "password": password}

    try:
        response = session.post(f"{base}{endpoint}", json=body, timeout=timeout)
    except requests.RequestException as error:
        raise AuthenticationError(f"auth request failed: {error}") from error

    # Two acceptance processes may start against a fresh database at once.
    # If another process won setup, use the normal login path immediately.
    if setup_required and response.status_code == 409:
        try:
            response = session.post(
                f"{base}/api/v1/auth/login",
                json={"email": email, "password": password},
                timeout=timeout,
            )
        except requests.RequestException as error:
            raise AuthenticationError(f"auth request failed: {error}") from error

    if response.status_code < 200 or response.status_code >= 300:
        raise AuthenticationError(f"auth request failed: {_response_code(response)}")
    try:
        user = response.json()
    except ValueError as error:
        raise AuthenticationError("auth request returned invalid JSON") from error
    if not isinstance(user, dict) or not user.get("id"):
        raise AuthenticationError("auth request returned an invalid user")
    if require_role and user.get("role") != require_role:
        raise AuthenticationError(f"live acceptance requires role={require_role}")
    return user
