"""
Tests for command functionality.

This module contains tests for:
- Command creation
- Command retrieval
- Command acknowledgment
- Authentication requirements
- Data validation
"""

import pytest
from fastapi import status
from datetime import datetime
from app.db.models import Tank, Command

@pytest.fixture
def registered_tank(client):
    """Create a registered tank for testing."""
    response = client.post(
        "/register",
        json={"name": "Command Test Tank"}
    )
    return response.json()

def test_create_command_success(client, registered_tank):
    """Test successful command creation."""
    response = client.post(
        f"/commands/{registered_tank['id']}",
        json={
            "command": "feed",
            "parameters": {"amount": 5, "duration": 30}
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "command_id" in data
    assert "created successfully" in data["message"].lower()

def test_create_command_invalid_tank(client):
    """Test command creation for non-existent tank."""
    response = client.post(
        "/commands/999",
        json={
            "command": "feed",
            "parameters": {"amount": 5}
        }
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_commands_success(client, registered_tank, db_session):
    """Test retrieving commands for a tank."""
    # Add some commands
    for i in range(3):
        command = Command(
            tank_id=registered_tank["id"],
            command="feed",
            parameters={"amount": i + 1}
        )
        db_session.add(command)
    db_session.commit()
    
    response = client.get(f"/commands/{registered_tank['id']}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3
    assert all(item["command"] == "feed" for item in data)
    assert all("parameters" in item for item in data)

def test_get_commands_unacknowledged_only(client, registered_tank, db_session):
    """Test retrieving only unacknowledged commands."""
    # Add acknowledged and unacknowledged commands
    for i in range(2):
        command = Command(
            tank_id=registered_tank["id"],
            command="feed",
            parameters={"amount": i + 1},
            acknowledged=i == 0
        )
        db_session.add(command)
    db_session.commit()
    
    response = client.get(
        f"/commands/{registered_tank['id']}",
        params={"unacknowledged_only": True}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert not data[0]["acknowledged"]

def test_acknowledge_command_success(client, registered_tank, db_session):
    """Test successful command acknowledgment."""
    # Create a command
    command = Command(
        tank_id=registered_tank["id"],
        command="feed",
        parameters={"amount": 5}
    )
    db_session.add(command)
    db_session.commit()
    
    response = client.post(
        f"/commands/{command.id}/ack",
        headers={"Authorization": f"Bearer {registered_tank['token']}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert "message" in response.json()
    assert "acknowledged successfully" in response.json()["message"].lower()
    
    # Verify command is acknowledged in database
    db_command = db_session.query(Command).filter(Command.id == command.id).first()
    assert db_command.acknowledged is True
    assert db_command.ack_time is not None

def test_acknowledge_command_unauthorized(client, registered_tank, db_session):
    """Test command acknowledgment without authentication."""
    # Create a command
    command = Command(
        tank_id=registered_tank["id"],
        command="feed",
        parameters={"amount": 5}
    )
    db_session.add(command)
    db_session.commit()
    
    response = client.post(f"/commands/{command.id}/ack")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_acknowledge_command_wrong_tank(client, registered_tank, db_session):
    """Test command acknowledgment by wrong tank."""
    # Create another tank
    other_tank = Tank(name="Other Tank", token="other-token")
    db_session.add(other_tank)
    db_session.flush()
    
    # Create a command for the first tank
    command = Command(
        tank_id=registered_tank["id"],
        command="feed",
        parameters={"amount": 5}
    )
    db_session.add(command)
    db_session.commit()
    
    response = client.post(
        f"/commands/{command.id}/ack",
        headers={"Authorization": f"Bearer {other_tank.token}"}
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_command_validation(client, registered_tank):
    """Test command creation data validation."""
    # Missing command field
    response = client.post(
        f"/commands/{registered_tank['id']}",
        json={"parameters": {"amount": 5}}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Invalid command type
    response = client.post(
        f"/commands/{registered_tank['id']}",
        json={"command": 123, "parameters": {"amount": 5}}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY 