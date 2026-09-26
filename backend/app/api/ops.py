from fastapi import APIRouter, Depends

from ..repositories.skill_calls import SkillCallRepository
from ..services.observability import RequestMetrics
from ..services.auth import require_admin

router = APIRouter(
    prefix="/api/v1/ops",
    tags=["operations"],
    dependencies=[Depends(require_admin)],
)
request_metrics: RequestMetrics | None = None


def set_request_metrics(metrics: RequestMetrics) -> None:
    global request_metrics
    request_metrics = metrics


@router.get("/metrics")
async def operational_metrics() -> dict:
    skill_metrics = await SkillCallRepository().summary()
    return {
        "service": (request_metrics.snapshot() if request_metrics else {}),
        "skills": skill_metrics,
    }
