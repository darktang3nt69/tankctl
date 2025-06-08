import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine, get_db
from sqlalchemy.orm import Session
from unittest.mock import patch

# Use a test database for isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(name="db_session")
def db_session_fixture():
    # Create the database tables before each test
    Base.metadata.create_all(bind=engine)
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()
        # Drop the database tables after each test
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

def test_read_main(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "AquaPi Tank API is running!"}

# TODO: Add more comprehensive API endpoint unit tests
# For example, test registration, status updates, command creation, etc.
# Mock external dependencies like Discord API calls if necessary.

def test_register_tank_success(client: TestClient):
    response = client.post(
        "/api/v1/tank/register",
        json={
            "tank_name": "TestTank1",
            "location": "Living Room",
            "firmware_version": "1.0.0"
        }
    )
    assert response.status_code == 200
    assert "tank_id" in response.json()
    assert "token" in response.json()
    assert response.json()["message"] == "Tank registered successfully"

def test_register_tank_duplicate_name(client: TestClient):
    # Register first tank
    client.post(
        "/api/v1/tank/register",
        json={
            "tank_name": "UniqueTank",
            "location": "Bedroom",
            "firmware_version": "1.0.0"
        }
    )
    # Try to register a second tank with the same name
    response = client.post(
        "/api/v1/tank/register",
        json={
            "tank_name": "UniqueTank",
            "location": "Kitchen",
            "firmware_version": "1.0.1"
        }
    )
    assert response.status_code == 409 # Conflict
    assert response.json()["detail"] == "Tank with this name already exists"

# TODO: Add tests for status updates, command issuance, etc. 