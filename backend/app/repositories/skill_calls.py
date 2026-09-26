import json
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any

from sqlalchemy import func, select

from ..db import SessionLocal, SkillCallRow, TripRow
from ..domain.models import SkillCallRecord, SkillResult
from ..skills.base import SkillContext


async def record_skill_call(
    adapter: str,
    result: SkillResult,
    context: SkillContext,
) -> None:
    async with SessionLocal() as session:
        owner_id = context.user_id
        if owner_id is None and context.trip_id:
            owner_id = await session.scalar(
                select(TripRow.user_id).where(TripRow.id == context.trip_id)
            )
        session.add(
            SkillCallRow(
                id=f"skillcall_{uuid4().hex[:12]}",
                user_id=owner_id,
                request_id=context.request_id,
                trip_id=context.trip_id,
                adapter=adapter,
                provider=result.provider,
                success=result.success,
                cache_hit=result.cache_hit,
                latency_ms=result.latency_ms,
                error_code=result.error_code,
                source_summary_json=json.dumps(
                    [
                        {"provider": source.provider, "title": source.title}
                        for source in result.sources
                    ],
                    ensure_ascii=False,
                ),
                created_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()


async def record_agent_call(
    adapter: str,
    *,
    user_id: str | None = None,
    provider: str = "configured",
    success: bool,
    latency_ms: int,
    usage: dict[str, Any] | None = None,
    error_code: str | None = None,
) -> None:
    """Persist model usage without storing prompts, responses or reasoning."""
    try:
        normalized_usage = {
            key: int(value or 0)
            for key, value in (usage or {}).items()
            if key in {
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "prompt_cache_hit_tokens",
                "prompt_cache_miss_tokens",
            }
        }
        async with SessionLocal() as session:
            session.add(
                SkillCallRow(
                    id=f"skillcall_{uuid4().hex[:12]}",
                    user_id=user_id,
                    request_id=None,
                    trip_id=None,
                    adapter=adapter,
                    provider=provider,
                    success=success,
                    cache_hit=bool(normalized_usage.get("prompt_cache_hit_tokens")),
                    latency_ms=max(0, int(latency_ms)),
                    error_code=error_code,
                    source_summary_json=json.dumps(
                        [{"kind": "token_usage", **normalized_usage}],
                        ensure_ascii=False,
                    ),
                    created_at=datetime.now(timezone.utc),
                )
            )
            await session.commit()
    except Exception:
        # Observability must never make an otherwise valid Agent call fail.
        # This also keeps isolated unit tests independent from a migrated DB.
        return


class SkillCallRepository:
    def __init__(self, user_id: str | None = None):
        self.user_id = user_id

    async def list(self, limit: int = 50) -> list[SkillCallRecord]:
        async with SessionLocal() as session:
            statement = select(SkillCallRow)
            if self.user_id is not None:
                statement = statement.where(SkillCallRow.user_id == self.user_id)
            statement = statement.order_by(SkillCallRow.created_at.desc()).limit(limit)
            rows = (await session.scalars(statement)).all()
        return [
            SkillCallRecord(
                id=row.id,
                request_id=row.request_id,
                trip_id=row.trip_id,
                adapter=row.adapter,
                provider=row.provider,
                success=row.success,
                cache_hit=row.cache_hit,
                latency_ms=row.latency_ms,
                error_code=row.error_code,
                source_summary=json.loads(row.source_summary_json),
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def summary(self) -> dict:
        async with SessionLocal() as session:
            owner_filter = (
                (SkillCallRow.user_id == self.user_id)
                if self.user_id is not None
                else None
            )
            total_statement = select(func.count()).select_from(SkillCallRow)
            successful_statement = select(func.count()).select_from(SkillCallRow).where(
                SkillCallRow.success.is_(True)
            )
            cached_statement = select(func.count()).select_from(SkillCallRow).where(
                SkillCallRow.cache_hit.is_(True)
            )
            latency_statement = select(func.avg(SkillCallRow.latency_ms))
            if owner_filter is not None:
                total_statement = total_statement.where(owner_filter)
                successful_statement = successful_statement.where(owner_filter)
                cached_statement = cached_statement.where(owner_filter)
                latency_statement = latency_statement.where(owner_filter)
            total = await session.scalar(total_statement)
            successful = await session.scalar(successful_statement)
            cached = await session.scalar(cached_statement)
            average_latency = await session.scalar(latency_statement)
            adapter_statement = select(SkillCallRow.adapter, func.count()).group_by(
                SkillCallRow.adapter
            )
            if owner_filter is not None:
                adapter_statement = adapter_statement.where(owner_filter)
            rows = (
                await session.execute(
                    adapter_statement
                    .order_by(func.count().desc())
                )
            ).all()
            audit_statement = select(SkillCallRow)
            if owner_filter is not None:
                audit_statement = audit_statement.where(owner_filter)
            audit_rows = list((await session.scalars(audit_statement)).all())
        agent_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "prompt_cache_hit_tokens": 0,
            "prompt_cache_miss_tokens": 0,
        }
        agent_calls = 0
        for row in audit_rows:
            # Agent rows are identified by their adapter namespace, so a
            # custom provider label (openrouter, ollama_cloud, self_hosted,
            # etc.) is included without maintaining a provider allow-list.
            if not str(row.adapter or "").startswith("agent."):
                continue
            agent_calls += 1
            try:
                summaries = json.loads(row.source_summary_json)
            except (TypeError, ValueError):
                continue
            for item in summaries if isinstance(summaries, list) else []:
                if not isinstance(item, dict) or item.get("kind") != "token_usage":
                    continue
                for key in agent_usage:
                    try:
                        agent_usage[key] += int(item.get(key) or 0)
                    except (TypeError, ValueError):
                        continue
        total_value = int(total or 0)
        return {
            "total_calls": total_value,
            "successful_calls": int(successful or 0),
            "failed_calls": max(0, total_value - int(successful or 0)),
            "cache_hits": int(cached or 0),
            "average_latency_ms": round(float(average_latency or 0), 2),
            "by_adapter": {adapter: int(count) for adapter, count in rows},
            "agent_calls": agent_calls,
            "agent_usage": agent_usage,
            "token_cost": {
                "unit": "tokens",
                "total": agent_usage["total_tokens"],
                "note": "Token 用量来自模型官方响应；未配置动态单价时不换算货币。",
            },
            "estimated_cost_usd": None,
            "cost_note": "工具调用保留数量与延迟；语义智能体另记录官方 Token 用量，不硬编码可能变化的模型价格。",
        }
