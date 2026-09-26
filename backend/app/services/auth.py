from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import Cookie, Depends, Response
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.errors import AppError
from ..db import (
    AuthSessionRow,
    FileRow,
    JobRow,
    SessionLocal,
    SkillCallRow,
    TripRow,
    TripVersionRow,
    UserRow,
    VehicleRow,
    get_session,
)
from ..domain.models import (
    AdminSetupRequest,
    AuthCredentials,
    ManagedUserCreate,
    User,
    UserRole,
)

AUTH_COOKIE_NAME = "rovia_session"
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_SALT_BYTES = 16


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SCRYPT_SALT_BYTES)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, raw_n, raw_r, raw_p, salt_hex, digest_hex = encoded.split("$", 5)
        if scheme != "scrypt":
            return False
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(raw_n),
            r=int(raw_r),
            p=int(raw_p),
        )
        return hmac.compare_digest(actual, bytes.fromhex(digest_hex))
    except (TypeError, ValueError):
        return False


def user_from_row(row: UserRow) -> User:
    return User(
        id=row.id,
        email=row.email,
        display_name=row.display_name,
        role=UserRole(row.role),
        is_active=row.is_active,
        created_at=row.created_at,
    )


async def user_row_by_email(session: AsyncSession, email: str) -> UserRow | None:
    return await session.scalar(
        select(UserRow).where(UserRow.email == normalize_email(email)).limit(1)
    )


async def count_users(session: AsyncSession) -> int:
    return int(await session.scalar(select(func.count()).select_from(UserRow)) or 0)


async def create_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    display_name: str,
    role: UserRole,
) -> User:
    normalized_email = normalize_email(email)
    if await user_row_by_email(session, normalized_email):
        raise AppError("USER_EMAIL_EXISTS", "这个邮箱已经注册", 409)
    now = datetime.now(timezone.utc)
    row = UserRow(
        id=f"user_{uuid4().hex[:12]}",
        email=normalized_email,
        display_name=display_name.strip(),
        password_hash=hash_password(password),
        role=role.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    await session.commit()
    return user_from_row(row)


async def authenticate(session: AsyncSession, credentials: AuthCredentials) -> User:
    row = await user_row_by_email(session, credentials.email)
    if not row or not row.is_active or not verify_password(credentials.password, row.password_hash):
        raise AppError("AUTH_INVALID_CREDENTIALS", "邮箱或密码不正确", 401)
    return user_from_row(row)


async def create_session(session: AsyncSession, user_id: str) -> str:
    raw_token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    session.add(
        AuthSessionRow(
            id=f"auth_{uuid4().hex[:12]}",
            user_id=user_id,
            token_hash=hashlib.sha256(raw_token.encode("utf-8")).hexdigest(),
            expires_at=now + timedelta(days=get_settings().auth_session_ttl_days),
            created_at=now,
        )
    )
    await session.commit()
    return raw_token


async def user_from_token(session: AsyncSession, raw_token: str | None) -> User | None:
    if not raw_token:
        return None
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    row = await session.scalar(
        select(UserRow)
        .join(AuthSessionRow, AuthSessionRow.user_id == UserRow.id)
        .where(
            AuthSessionRow.token_hash == token_hash,
            AuthSessionRow.expires_at > datetime.now(timezone.utc),
            UserRow.is_active.is_(True),
        )
        .limit(1)
    )
    return user_from_row(row) if row else None


def set_auth_cookie(response: Response, raw_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        AUTH_COOKIE_NAME,
        raw_token,
        max_age=settings.auth_session_ttl_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )


async def get_optional_user(
    session: AsyncSession = Depends(get_session),
    raw_token: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME),
) -> User | None:
    return await user_from_token(session, raw_token)


async def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if not user:
        raise AppError("AUTH_REQUIRED", "请先登录", 401)
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise AppError("ADMIN_REQUIRED", "只有管理员可以执行此操作", 403)
    return user


async def logout_token(session: AsyncSession, raw_token: str | None) -> None:
    if not raw_token:
        return
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    await session.execute(delete(AuthSessionRow).where(AuthSessionRow.token_hash == token_hash))
    await session.commit()


async def migrate_legacy_data(session: AsyncSession, admin_id: str) -> int:
    """Assign rows from the pre-auth schema to the first administrator."""
    migrated = 0
    for model in (TripRow, TripVersionRow, VehicleRow, FileRow, JobRow, SkillCallRow):
        result = await session.execute(
            update(model)
            .where(model.user_id.is_(None))
            .values(user_id=admin_id)
        )
        migrated += int(result.rowcount or 0)
    await session.commit()
    return migrated


async def ensure_configured_admin() -> None:
    """Create an env-configured admin and migrate old rows during service boot."""
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        return
    async with SessionLocal() as session:
        row = await user_row_by_email(session, settings.admin_email)
        if row is None:
            user = await create_user(
                session,
                email=settings.admin_email,
                password=settings.admin_password,
                display_name=settings.admin_display_name,
                role=UserRole.admin,
            )
            await migrate_legacy_data(session, user.id)
        else:
            admin = await session.scalar(
                select(UserRow).where(UserRow.role == UserRole.admin.value).limit(1)
            )
            if admin:
                await migrate_legacy_data(session, admin.id)


async def setup_admin(session: AsyncSession, payload: AdminSetupRequest) -> User:
    if await count_users(session):
        raise AppError("AUTH_ALREADY_INITIALIZED", "管理员账户已经初始化", 409)
    user = await create_user(
        session,
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
        role=UserRole.admin,
    )
    await migrate_legacy_data(session, user.id)
    return user


async def list_users(session: AsyncSession) -> list[User]:
    rows = (
        await session.scalars(select(UserRow).order_by(UserRow.created_at.asc()))
    ).all()
    return [user_from_row(row) for row in rows]
