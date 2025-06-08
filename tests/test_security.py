import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import Base, engine, get_db
from app.core.config import settings
from unittest.mock import patch
import uuid

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

# Mock the preshared key for testing
@pytest.fixture(autouse=True)
def mock_preshared_key():
    with patch.dict(settings.model_dump(), {"TANK_PRESHARED_KEY": "test_preshared_key"}):
        yield

# Mock the admin API key for testing
@pytest.fixture(autouse=True)
def mock_admin_api_key():
    with patch.dict(settings.model_dump(), {"ADMIN_API_KEY": "test_admin_api_key"}):
        yield

def test_register_tank_invalid_auth_key(client: TestClient):
    response = client.post(
        "/api/v1/tank/register",
        json={
            "auth_key": "wrong_key",
            "tank_name": "AuthTestTank",
            "location": "Location",
            "firmware_version": "1.0.0"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid pre-shared key"

def test_protected_endpoint_no_token(client: TestClient):
    response = client.post(
        "/api/v1/tank/some_protected_endpoint", # Replace with an actual protected endpoint that uses get_current_tank
        json={}
    )
    assert response.status_code == 401
    assert "not found" in response.json()["detail"] # Check for "Not Found" or similar if endpoint doesn't exist

def test_protected_endpoint_invalid_jwt(client: TestClient):
    response = client.post(
        "/api/v1/tank/some_protected_endpoint", # Replace with an actual protected endpoint
        json={},
        headers={
            "Authorization": "Bearer invalid.jwt.token"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials" # If the endpoint expects a valid JWT

def test_admin_endpoint_no_api_key(client: TestClient):
    response = client.post(
        "/api/v1/admin/send_command_to_tank", # An actual admin endpoint
        json={
            "tank_id": str(uuid.uuid4()),
            "command_payload": "test_command"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated" # This is the default FastAPI response for missing header dependency

def test_admin_endpoint_invalid_api_key(client: TestClient):
    response = client.post(
        "/api/v1/admin/send_command_to_tank",
        json={
            "tank_id": str(uuid.uuid4()),
            "command_payload": "test_command"
        },
        headers={
            "x-api-key": "wrong_admin_key"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized: Invalid Admin API Key" 