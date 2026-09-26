from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import VehicleRow
from ..domain.models import VehicleProfile, VehicleUpdate


class VehicleRepository:
    def __init__(self, session: AsyncSession, user_id: str | None = None):
        self.session = session
        self.user_id = user_id

    async def create(self, vehicle: VehicleProfile, user_id: str | None = None) -> VehicleProfile:
        now = datetime.now(timezone.utc)
        self.session.add(
            VehicleRow(
                id=vehicle.id,
                user_id=self.user_id if self.user_id is not None else user_id,
                brand=vehicle.brand,
                series=vehicle.series,
                model=vehicle.model,
                power_type=vehicle.power_type,
                document=vehicle.model_dump_json(),
                created_at=now,
                updated_at=now,
            )
        )
        await self.session.commit()
        return vehicle

    async def list(self, user_id: str | None = None) -> list[VehicleProfile]:
        statement = select(VehicleRow).order_by(VehicleRow.updated_at.desc())
        owner_id = self.user_id if self.user_id is not None else user_id
        if owner_id is not None:
            statement = statement.where(VehicleRow.user_id == owner_id)
        rows = (await self.session.scalars(statement)).all()
        return [VehicleProfile.model_validate_json(row.document) for row in rows]

    async def _get_row(self, vehicle_id: str) -> VehicleRow | None:
        statement = select(VehicleRow).where(VehicleRow.id == vehicle_id)
        if self.user_id is not None:
            statement = statement.where(VehicleRow.user_id == self.user_id)
        return await self.session.scalar(statement)

    async def get(self, vehicle_id: str) -> VehicleProfile | None:
        row = await self._get_row(vehicle_id)
        return VehicleProfile.model_validate_json(row.document) if row else None

    async def update(self, vehicle_id: str, payload: VehicleUpdate) -> VehicleProfile | None:
        row = await self._get_row(vehicle_id)
        if not row:
            return None
        vehicle = VehicleProfile.model_validate_json(row.document).model_copy(
            update=payload.model_dump(exclude_none=True),
        )
        row.brand = vehicle.brand
        row.series = vehicle.series
        row.model = vehicle.model
        row.power_type = vehicle.power_type
        row.document = vehicle.model_dump_json()
        row.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        return vehicle

    async def delete(self, vehicle_id: str) -> bool:
        row = await self._get_row(vehicle_id)
        if not row:
            return False
        await self.session.delete(row)
        await self.session.commit()
        return True
