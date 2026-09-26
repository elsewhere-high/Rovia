from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.errors import AppError
from ..db import AuthSessionRow, UserRow, get_session
from ..domain.models import (
    AdminSetupRequest,
    AuthCredentials,
    AuthStatus,
    ManagedUserCreate,
    User,
    UserRole,
)
from ..services.auth import (
    AUTH_COOKIE_NAME,
    authenticate,
    count_users,
    create_session,
    create_user,
    get_current_user,
    get_optional_user,
    list_users,
    logout_token,
    require_admin,
    set_auth_cookie,
    setup_admin,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/status", response_model=AuthStatus)
async def auth_status(
    session: AsyncSession = Depends(get_session),
    user: User | None = Depends(get_optional_user),
) -> AuthStatus:
    return AuthStatus(
        setup_required=await count_users(session) == 0,
        authenticated=user is not None,
        user=user,
    )


@router.post("/setup", response_model=User, status_code=status.HTTP_201_CREATED)
async def initialize_admin(
    payload: AdminSetupRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> User:
    user = await setup_admin(session, payload)
    set_auth_cookie(response, await create_session(session, user.id))
    return user


@router.post("/login", response_model=User)
async def login(
    payload: AuthCredentials,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> User:
    user = await authenticate(session, payload)
    set_auth_cookie(response, await create_session(session, user.id))
    return user


@router.get("/me", response_model=User)
async def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    session: AsyncSession = Depends(get_session),
    raw_token: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME),
) -> Response:
    await logout_token(session, raw_token)
    response.delete_cookie(AUTH_COOKIE_NAME, path="/")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users", response_model=list[User])
async def managed_users(
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[User]:
    return await list_users(session)


@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_managed_user(
    payload: ManagedUserCreate,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> User:
    return await create_user(
        session,
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
        role=UserRole.user,
    )
