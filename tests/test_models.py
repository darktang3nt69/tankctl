import pytest
from sqlalchemy.orm import Session
from app.models.tank import Tank
from app.core.database import Base, engine
import uuid
from datetime import datetime
from app.utils.timezone import IST

# Use a test database for isolation
# This fixture is similar to the one in test_api_endpoints.py but specific for model tests
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

def test_create_tank(db_session: Session):
    tank = Tank(
        tank_name="TestTank",
        location="Living Room",
        firmware_version="1.0.0",
        last_seen=datetime.now(IST),
        is_online=True
    )
    db_session.add(tank)
    db_session.commit()
    db_session.refresh(tank)

    assert tank.tank_id is not None
    assert tank.tank_name == "TestTank"
    assert tank.location == "Living Room"
    assert tank.firmware_version == "1.0.0"
    assert tank.last_seen.tzinfo == IST
    assert tank.is_online == True

def test_read_tank(db_session: Session):
    tank_id = uuid.uuid4()
    tank = Tank(
        tank_id=tank_id,
        tank_name="ReadTank",
        location="Bedroom",
        firmware_version="1.0.1"
    )
    db_session.add(tank)
    db_session.commit()

    retrieved_tank = db_session.query(Tank).filter(Tank.tank_id == tank_id).first()
    assert retrieved_tank is not None
    assert retrieved_tank.tank_name == "ReadTank"

def test_update_tank(db_session: Session):
    tank_id = uuid.uuid4()
    tank = Tank(
        tank_id=tank_id,
        tank_name="UpdateTank",
        location="Kitchen",
        firmware_version="1.0.2"
    )
    db_session.add(tank)
    db_session.commit()

    tank.location = "Dining Room"
    db_session.add(tank)
    db_session.commit()
    db_session.refresh(tank)

    assert tank.location == "Dining Room"

def test_delete_tank(db_session: Session):
    tank_id = uuid.uuid4()
    tank = Tank(
        tank_id=tank_id,
        tank_name="DeleteTank",
        location="Garage",
        firmware_version="1.0.3"
    )
    db_session.add(tank)
    db_session.commit()

    db_session.delete(tank)
    db_session.commit()

    deleted_tank = db_session.query(Tank).filter(Tank.tank_id == tank_id).first()
    assert deleted_tank is None

# TODO: Add tests for other models like TankCommand, StatusLog, TankSettings, etc. 