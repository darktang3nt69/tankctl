"""
Tests for tank status functionality.

This module contains tests for:
- Status update endpoint
- Status retrieval endpoints
- Authentication requirements
- Data validation
"""

import pytest
from fastapi import status
from datetime import datetime, timedelta
from app.db.models import Tank, TankStatus

@pytest.fixture
def registered_tank(client):
    """Create a registered tank for testing."""
    response = client.post(
        "/register",
        json={"name": "Status Test Tank"}
    )
    return response.json()

def test_update_status_success(client, registered_tank):
    """Test successful status update."""
    response = client.post(
        "/status",
        json={"status": {"temperature": 25.5, "ph": 7.2}},
        headers={"Authorization": f"Bearer {registered_tank['token']}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert "message" in response.json()
    assert "updated successfully" in response.json()["message"].lower()

def test_update_status_unauthorized(client):
    """Test status update without authentication."""
    response = client.post(
        "/status",
        json={"status": {"temperature": 25.5, "ph": 7.2}}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_update_status_invalid_token(client, registered_tank):
    """Test status update with invalid token."""
    response = client.post(
        "/status",
        json={"status": {"temperature": 25.5, "ph": 7.2}},
        headers={"Authorization": "Bearer invalid-token"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_tank_status(client, registered_tank, db_session):
    """Test retrieving status for a specific tank."""
    # Add some status updates
    for i in range(3):
        status = TankStatus(
            tank_id=registered_tank["id"],
            status={"temperature": 25.0 + i, "ph": 7.0}
        )
        db_session.add(status)
    db_session.commit()
    
    response = client.get(f"/status/{registered_tank['id']}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3
    assert all("temperature" in item["status"] for item in data)
    assert all("ph" in item["status"] for item in data)

def test_get_all_statuses(client, registered_tank, db_session):
    """Test retrieving status for all tanks."""
    # Add status updates for multiple tanks
    for i in range(2):
        tank = Tank(name=f"Status Tank {i}", token=f"token-{i}")
        db_session.add(tank)
        db_session.flush()
        
        status = TankStatus(
            tank_id=tank.id,
            status={"temperature": 25.0, "ph": 7.0}
        )
        db_session.add(status)
    db_session.commit()
    
    response = client.get("/status/all")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2  # At least 2 status updates

def test_status_update_updates_last_seen(client, registered_tank, db_session):
    """Test that status update updates the last_seen timestamp."""
    before_update = datetime.utcnow()
    
    response = client.post(
        "/status",
        json={"status": {"temperature": 25.5, "ph": 7.2}},
        headers={"Authorization": f"Bearer {registered_tank['token']}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    tank = db_session.query(Tank).filter(Tank.id == registered_tank["id"]).first()
    assert tank.last_seen is not None
    assert tank.last_seen > before_update

def test_status_update_validation(client, registered_tank):
    """Test status update data validation."""
    # Missing status field
    response = client.post(
        "/status",
        json={},
        headers={"Authorization": f"Bearer {registered_tank['token']}"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Invalid status data
    response = client.post(
        "/status",
        json={"status": "invalid"},
        headers={"Authorization": f"Bearer {registered_tank['token']}"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY 