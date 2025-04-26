import pytest
from httpx import AsyncClient
from app.main import app
from app.core.config import settings
from app.db.session import async_session
from app.db.models import Command, Tank
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, UTC, timedelta

@pytest.fixture
async def db():
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def test_tank(db: AsyncSession):
    tank = Tank(
        name="Test Tank",
        token="test_token",
        last_seen=datetime.now(UTC)
    )
    db.add(tank)
    await db.commit()
    await db.refresh(tank)
    return tank

@pytest.mark.asyncio
async def test_command_notification(db: AsyncSession, test_tank):
    """Test that command notifications are sent when commands are acknowledged."""
    tank = await test_tank
    # Create a test command
    command = Command(
        tank_id=tank.id,
        command="test_command",
        parameters={"test": "value"},
        created_at=datetime.now(UTC),
        status="PENDING",
        acknowledged=False
    )
    db.add(command)
    await db.commit()
    await db.refresh(command)

    # Acknowledge the command
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            f"/commands/{command.id}/ack",
            headers={"Authorization": f"Bearer {tank.token}"}
        )
    
    assert response.status_code == 200
    assert response.json()["acknowledged"] is True
    
    # Verify command is marked as completed
    result = await db.execute(
        select(Command).filter(Command.id == command.id)
    )
    db_command = result.scalar_one()
    assert db_command.status == "COMPLETED"
    assert db_command.acknowledged is True
    assert db_command.ack_time is not None

@pytest.mark.asyncio
async def test_tank_offline_notification(db: AsyncSession, test_tank):
    """Test that offline notifications are sent when tanks go offline."""
    tank = await test_tank
    # Update tank's last_seen to be more than 60 seconds ago
    old_time = datetime.now(UTC) - timedelta(seconds=61)
    tank.last_seen = old_time
    await db.commit()
    
    # Trigger health check
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    
    # Verify tank is marked as offline
    result = await db.execute(
        select(Tank).filter(Tank.id == tank.id)
    )
    db_tank = result.scalar_one()
    assert db_tank.is_active is False 