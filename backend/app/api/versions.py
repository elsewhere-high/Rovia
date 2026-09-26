from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.errors import AppError
from ..db import TripRow, get_session
from ..domain.models import Trip, TripVersion, TripVersionCreate, User
from ..repositories import TripRepository
from ..repositories.versions import TripVersionRepository
from ..services.auth import get_current_user

router = APIRouter(
    prefix="/api/v1/trips/{trip_id}/versions",
    tags=["versions"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=TripVersion, status_code=status.HTTP_201_CREATED)
async def create_version(
    trip_id: str,
    payload: TripVersionCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> TripVersion:
    trip_repo = TripRepository(session, user.id)
    trip = await trip_repo.get(trip_id)
    if not trip:
        raise AppError("TRIP_NOT_FOUND", "行程不存在", 404)
    row = await session.scalar(
        select(TripRow).where(TripRow.id == trip_id, TripRow.user_id == user.id)
    )
    assert row is not None
    return await TripVersionRepository(session, user.id).create(
        trip,
        payload,
        row.state_json,
        row.plan_markdown,
    )


@router.get("", response_model=list[TripVersion])
async def list_versions(
    trip_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[TripVersion]:
    if not await TripRepository(session, user.id).get(trip_id):
        raise AppError("TRIP_NOT_FOUND", "行程不存在", 404)
    return await TripVersionRepository(session, user.id).list(trip_id)


@router.post("/{version_id}/restore", response_model=Trip)
async def restore_version(
    trip_id: str,
    version_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> Trip:
    return await TripVersionRepository(session, user.id).restore(trip_id, version_id)
