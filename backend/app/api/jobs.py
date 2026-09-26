from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.errors import AppError
from ..db import get_session
from ..domain.models import JobCreate, JobRecord, User
from ..repositories import JobRepository, TripRepository
from ..services.job_queue import enqueue_job
from ..services.auth import get_current_user

router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["jobs"],
    dependencies=[Depends(get_current_user)],
)


def get_repo(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> JobRepository:
    return JobRepository(session, user.id)


@router.post("", response_model=JobRecord, status_code=status.HTTP_202_ACCEPTED)
async def create_job(
    payload: JobCreate,
    repo: JobRepository = Depends(get_repo),
) -> JobRecord:
    if payload.kind == "planning" and payload.trip_id and not await TripRepository(
        repo.session,
        repo.user_id,
    ).get(payload.trip_id):
        raise AppError("TRIP_NOT_FOUND", "行程不存在", 404)
    record = await repo.create(payload)
    await enqueue_job(record)
    return record


@router.get("/{job_id}", response_model=JobRecord)
async def get_job(
    job_id: str,
    repo: JobRepository = Depends(get_repo),
) -> JobRecord:
    record = await repo.get(job_id)
    if not record:
        raise AppError("JOB_NOT_FOUND", "任务不存在", 404, {"job_id": job_id})
    return record


@router.post("/{job_id}/cancel", response_model=JobRecord)
async def cancel_job(
    job_id: str,
    repo: JobRepository = Depends(get_repo),
) -> JobRecord:
    record = await repo.cancel(job_id)
    if not record:
        raise AppError("JOB_NOT_FOUND", "任务不存在", 404, {"job_id": job_id})
    return record
