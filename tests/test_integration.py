import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import Base, engine, get_db
from app.models.tank import Tank
from app.models.status_log import StatusLog
from app.models.tank_command import TankCommand
from app.schemas.status import StatusUpdateRequest
from app.schemas.command import CommandIssueRequest, CommandAcknowledgeRequest
from app.utils.timezone import IST
from datetime import datetime, timedelta
import uuid
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

@pytest.fixture(name="client")
def client_fixture(db_session: Session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def register_test_tank(client: TestClient):
    response = client.post(
        "/api/v1/tank/register",
        json={
            "tank_name": "IntegrationTestTank",
            "location": "Lab",
            "firmware_version": "1.0.0"
        }
    )
    assert response.status_code == 200
    return response.json() # Returns tank_id and token

@patch("app.utils.discord.send_discord_embed")
def test_end_to_end_data_flow(mock_send_discord_embed, client: TestClient, db_session: Session, register_test_tank: dict):
    tank_id = register_test_tank["tank_id"]
    tank_token = register_test_tank["token"]

    # 1. Simulate status update
    status_update_payload = {
        "temperature": 25.5,
        "ph": 7.2,
        "light_state": True,
        "firmware_version": "1.0.1"
    }
    response = client.post(
        f"/api/v1/tank/{tank_id}/status",
        json=status_update_payload,
        headers={
            "Authorization": f"Bearer {tank_token}"
        }
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Tank status updated successfully"

    # Verify status log entry in DB
    status_log = db_session.query(StatusLog).filter(StatusLog.tank_id == tank_id).order_by(StatusLog.timestamp.desc()).first()
    assert status_log is not None
    assert status_log.temperature == 25.5
    assert status_log.ph == 7.2
    assert status_log.light_state == True
    assert status_log.firmware_version == "1.0.1"
    assert status_log.timestamp.tzinfo == IST # Ensure timezone awareness

    # Verify tank last_seen and other fields updated
    updated_tank = db_session.query(Tank).filter(Tank.tank_id == tank_id).first()
    assert updated_tank.last_seen.tzinfo == IST # Ensure timezone awareness
    assert updated_tank.is_online == True

    # 2. Simulate command issuance (e.g., from admin API)
    command_issue_payload = {
        "tank_id": tank_id,
        "command_payload": "light_off"
    }
    # Assuming an admin API key for this, replace with actual mechanism if different
    response = client.post(
        "/api/v1/admin/send_command_to_tank", # Assuming this endpoint exists based on earlier tasks
        json=command_issue_payload,
        headers={
            "x-api-key": "supersecretgrafanakey123" # Use your actual admin API key
        }
    )
    assert response.status_code == 200
    command_id = response.json()["command_id"]
    assert command_id is not None

    # Verify command in DB
    issued_command = db_session.query(TankCommand).filter(TankCommand.command_id == command_id).first()
    assert issued_command is not None
    assert issued_command.command_payload == "light_off"
    assert issued_command.status == "pending"
    assert issued_command.created_at.tzinfo == IST # Ensure timezone awareness

    # 3. Simulate tank polling for command
    response = client.get(
        f"/api/v1/tank/{tank_id}/command",
        headers={
            "Authorization": f"Bearer {tank_token}"
        }
    )
    assert response.status_code == 200
    polled_command = response.json()
    assert polled_command["command_id"] == str(command_id)
    assert polled_command["command_payload"] == "light_off"

    # 4. Simulate tank acknowledging command
    ack_payload = {
        "command_id": command_id,
        "success": True
    }
    response = client.post(
        f"/api/v1/tank/{tank_id}/command/acknowledge",
        json=ack_payload,
        headers={
            "Authorization": f"Bearer {tank_token}"
        }
    )
    assert response.status_code == 200
    assert "SUCCESS" in response.json()["message"]

    # Verify command status updated in DB
    acknowledged_command = db_session.query(TankCommand).filter(TankCommand.command_id == command_id).first()
    assert acknowledged_command.status == "success"

    # 5. Test command history retrieval
    response = client.get(
        f"/api/v1/tank/{tank_id}/commands/history",
        headers={
            "Authorization": f"Bearer {tank_token}" # Or ADMIN_API_KEY if this endpoint requires it
        }
    )
    assert response.status_code == 200
    history = response.json()
    assert len(history) >= 1 # At least one command should be in history
    assert history[0]["command_id"] == str(command_id)
    assert history[0]["created_at"].endswith('+05:30') or history[0]["created_at"].endswith('-00:00') or history[0]["created_at"].endswith('Z') # Check for IST offset or Z for UTC if not converted by custom encoder

    # TODO: Add more checks for historical data, scheduled events, etc. 