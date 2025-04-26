from uuid import UUID
from sqlalchemy import func, select
from app.db.models import Command, Tank, Metric, TankStatus, Alert
from typing import List, Dict, Optional
from app.db.session import async_session

async def get_command_queue_size(tank_id: UUID) -> int:
    """Get the number of pending commands for a tank."""
    async with async_session() as session:
        result = await session.execute(
            select(func.count(Command.id))
            .where(Command.tank_id == tank_id)
            .where(Command.acknowledged == False)
        )
        return result.scalar() or 0

async def get_all_tanks() -> List[Tank]:
    """Get all tanks."""
    async with async_session() as session:
        result = await session.execute(select(Tank))
        return result.scalars().all()

async def update_metric(tank_id: UUID, name: str, value: float) -> None:
    """Update a metric for a tank."""
    async with async_session() as session:
        metric = Metric(tank_id=tank_id, name=name, value=value)
        session.add(metric)
        await session.commit()

async def get_latest_metrics(tank_id: UUID) -> Dict[str, float]:
    """Get the latest metrics for a tank."""
    async with async_session() as session:
        result = await session.execute(
            select(Metric.name, Metric.value)
            .where(Metric.tank_id == tank_id)
            .order_by(Metric.timestamp.desc())
            .limit(1)
        )
        return {row[0]: row[1] for row in result.all()}

async def get_command_history(tank_id: UUID, limit: int = 10) -> List[Command]:
    """Get the command history for a tank."""
    async with async_session() as session:
        result = await session.execute(
            select(Command)
            .where(Command.tank_id == tank_id)
            .order_by(Command.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

async def get_latest_status(tank_id: UUID) -> Optional[TankStatus]:
    """Get the latest status for a tank."""
    async with async_session() as session:
        result = await session.execute(
            select(TankStatus)
            .where(TankStatus.tank_id == tank_id)
            .order_by(TankStatus.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

async def get_latest_alerts(tank_id: UUID, limit: int = 10) -> List[Alert]:
    """Get the latest alerts for a tank."""
    async with async_session() as session:
        result = await session.execute(
            select(Alert)
            .where(Alert.tank_id == tank_id)
            .order_by(Alert.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

async def get_latest_metrics_list(tank_id: UUID, limit: int = 10) -> List[Metric]:
    """Get the latest metrics for a tank."""
    async with async_session() as session:
        result = await session.execute(
            select(Metric)
            .where(Metric.tank_id == tank_id)
            .order_by(Metric.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all() 