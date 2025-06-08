import pytest
from sqlalchemy.orm import Session
from app.models.tank import Tank
from app.models.tank_command import TankCommand
from app.models.tank_settings import TankSettings
from app.services.command_service import issue_command, get_pending_command_for_tank, acknowledge_command, retry_stale_commands
from app.core.database import Base, engine
from app.schemas.command import CommandAcknowledgeRequest
import uuid
from datetime import datetime, timedelta
from app.utils.timezone import IST
from unittest.mock import patch

# Use a test database for isolation
@pytest.fixture(name="db_session")
def db_session_fixture():
    Base.metadata.create_all(bind=engine)
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def setup_tank(db_session: Session):
    tank_id = uuid.uuid4()
    tank = Tank(
        tank_id=tank_id,
        tank_name="TestTank",
        location="Living Room",
        firmware_version="1.0.0"
    )
    db_session.add(tank)
    db_session.commit()
    db_session.refresh(tank)
    return tank

@patch("app.utils.discord.send_discord_embed")
def test_issue_command_system_source(mock_send_discord_embed, db_session: Session, setup_tank: Tank):
    command = issue_command(db_session, setup_tank.tank_id, "feed_now", source="system")
    assert command.command_payload == "feed_now"
    assert command.status == "pending"
    assert command.tank_id == setup_tank.tank_id
    assert command.next_retry_at is not None
    mock_send_discord_embed.assert_not_called()

@patch("app.utils.discord.send_discord_embed")
def test_issue_command_manual_source_light_on(mock_send_discord_embed, db_session: Session, setup_tank: Tank):
    # Ensure settings exist for the tank
    settings = TankSettings(tank_id=setup_tank.tank_id)
    db_session.add(settings)
    db_session.commit()
    db_session.refresh(settings)

    command = issue_command(db_session, setup_tank.tank_id, "light_on", source="manual")
    assert command.command_payload == "light_on"
    db_session.refresh(settings)
    assert settings.manual_override_state == "on"
    mock_send_discord_embed.assert_not_called()

@patch("app.utils.discord.send_discord_embed")
def test_issue_command_manual_source_light_off(mock_send_discord_embed, db_session: Session, setup_tank: Tank):
    # Ensure settings exist for the tank
    settings = TankSettings(tank_id=setup_tank.tank_id)
    db_session.add(settings)
    db_session.commit()
    db_session.refresh(settings)

    command = issue_command(db_session, setup_tank.tank_id, "light_off", source="manual")
    assert command.command_payload == "light_off"
    db_session.refresh(settings)
    assert settings.manual_override_state == "off"
    mock_send_discord_embed.assert_not_called()

def test_issue_command_tank_not_found(db_session: Session):
    with pytest.raises(ValueError, match="Tank with ID.*not found"):
        issue_command(db_session, uuid.uuid4(), "feed_now")

def test_get_pending_command_for_tank(db_session: Session, setup_tank: Tank):
    issue_command(db_session, setup_tank.tank_id, "command_1")
    issue_command(db_session, setup_tank.tank_id, "command_2")

    pending_command = get_pending_command_for_tank(db_session, setup_tank.tank_id)
    assert pending_command is not None
    assert pending_command.command_payload == "command_1" # Should get the oldest pending

def test_acknowledge_command_success(db_session: Session, setup_tank: Tank):
    command = issue_command(db_session, setup_tank.tank_id, "test_ack_cmd")
    db_session.refresh(command)

    ack_request = CommandAcknowledgeRequest(command_id=command.command_id, success=True)
    result = acknowledge_command(db_session, str(setup_tank.tank_id), ack_request)

    db_session.refresh(command)
    assert command.status == "success"
    assert result["message"] == "Command `test_ack_cmd` acknowledged as SUCCESS"

def test_acknowledge_command_failed(db_session: Session, setup_tank: Tank):
    command = issue_command(db_session, setup_tank.tank_id, "test_fail_cmd")
    db_session.refresh(command)

    ack_request = CommandAcknowledgeRequest(command_id=command.command_id, success=False)
    result = acknowledge_command(db_session, str(setup_tank.tank_id), ack_request)

    db_session.refresh(command)
    assert command.status == "failed"
    assert result["message"] == "Command `test_fail_cmd` acknowledged as FAILED"

def test_acknowledge_command_not_found(db_session: Session, setup_tank: Tank):
    ack_request = CommandAcknowledgeRequest(command_id=uuid.uuid4(), success=True)
    with pytest.raises(ValueError, match="Command not found."):
        acknowledge_command(db_session, str(setup_tank.tank_id), ack_request)

def test_acknowledge_command_wrong_tank(db_session: Session, setup_tank: Tank):
    command = issue_command(db_session, setup_tank.tank_id, "test_wrong_tank_cmd")
    db_session.refresh(command)

    wrong_tank_id = uuid.uuid4()
    ack_request = CommandAcknowledgeRequest(command_id=command.command_id, success=True)
    with pytest.raises(ValueError, match="Command does not belong to this tank."):
        acknowledge_command(db_session, str(wrong_tank_id), ack_request)

@patch("app.utils.discord.send_discord_embed")
def test_retry_stale_commands_success(mock_send_discord_embed, db_session: Session, setup_tank: Tank):
    # Create a stale command
    stale_command = TankCommand(
        tank_id=setup_tank.tank_id,
        command_payload="stale_cmd",
        status="pending",
        retries=0,
        next_retry_at=datetime.now(IST) - timedelta(minutes=5)
    )
    db_session.add(stale_command)
    db_session.commit()

    retry_stale_commands(db_session)
    db_session.refresh(stale_command)

    assert stale_command.status == "delivered"
    assert stale_command.retries == 1
    assert stale_command.next_retry_at > datetime.now(IST) - timedelta(minutes=1) # Should be in the future
    mock_send_discord_embed.assert_called_once_with(
        status="retry_scheduled",
        tank_name=setup_tank.tank_name,
        command_payload="stale_cmd",
        extra_fields={
            "Retries": "1",
            "Next Retry": stale_command.next_retry_at.strftime("%Y-%m-%d %H:%M:%S IST")
        }
    )

@patch("app.utils.discord.send_discord_embed")
def test_retry_stale_commands_max_retries(mock_send_discord_embed, db_session: Session, setup_tank: Tank):
    # Create a command that has exceeded max retries
    failed_command = TankCommand(
        tank_id=setup_tank.tank_id,
        command_payload="failed_cmd",
        status="pending",
        retries=3, # MAX_RETRIES from command_service is 3 by default
        next_retry_at=datetime.now(IST) - timedelta(minutes=5)
    )
    db_session.add(failed_command)
    db_session.commit()

    retry_stale_commands(db_session)
    db_session.refresh(failed_command)

    assert failed_command.status == "failed"
    assert failed_command.retries == 3
    mock_send_discord_embed.assert_called_once_with(
        status="retry_failed",
        tank_name=setup_tank.tank_name,
        command_payload="failed_cmd",
        extra_fields={
            "Retries": "3",
            "Status": "Permanently failed"
        }
    ) 