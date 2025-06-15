from sqlalchemy.orm import Session
from app.models.tank import Tank
import uuid

def get_tank_by_id(db: Session, tank_id: uuid.UUID):
    """
    Retrieve a tank by its ID.
    """
    return db.query(Tank).filter(Tank.tank_id == tank_id).first() 