"""
Tests for tank registration functionality.

This module contains tests for:
- Tank registration endpoint
- Duplicate tank name handling
- Token generation
- Response validation
"""

import pytest
from fastapi import status
from app.db.models import Tank

def test_register_tank_success(client):
    """Test successful tank registration."""
    response = client.post(
        "/register",
        json={"name": "Test Tank 1"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert "id" in data
    assert data["name"] == "Test Tank 1"
    assert "token" in data
    assert len(data["token"]) > 0

def test_register_tank_duplicate_name(client):
    """Test registration with duplicate tank name."""
    # Register first tank
    client.post("/register", json={"name": "Test Tank 2"})
    
    # Try to register with same name
    response = client.post(
        "/register",
        json={"name": "Test Tank 2"}
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "detail" in response.json()
    assert "already registered" in response.json()["detail"].lower()

def test_register_tank_invalid_name(client):
    """Test registration with invalid tank name."""
    # Empty name
    response = client.post(
        "/register",
        json={"name": ""}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Name too long
    long_name = "a" * 101  # Assuming max length is 100
    response = client.post(
        "/register",
        json={"name": long_name}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_register_tank_token_uniqueness(client, db_session):
    """Test that generated tokens are unique."""
    # Register multiple tanks
    tokens = set()
    for i in range(5):
        response = client.post(
            "/register",
            json={"name": f"Test Tank {i+3}"}
        )
        assert response.status_code == status.HTTP_200_OK
        tokens.add(response.json()["token"])
    
    # Verify all tokens are unique
    assert len(tokens) == 5

def test_register_tank_database_integrity(client, db_session):
    """Test database integrity after tank registration."""
    # Register a tank
    response = client.post(
        "/register",
        json={"name": "Test Tank 4"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify tank exists in database
    tank = db_session.query(Tank).filter(Tank.id == data["id"]).first()
    assert tank is not None
    assert tank.name == data["name"]
    assert tank.token == data["token"]
    assert tank.is_active is True
    assert tank.config == {} 