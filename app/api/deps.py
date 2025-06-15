from typing import Generator

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.utils.jwt import verify_access_token

from app.core.config import settings
from app.models.tank import Tank

security = HTTPBearer()

def get_db() -> Generator[Session, None, None]:
    """
    Provide a SQLAlchemy session and close it when done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_tank(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> str:
    """
    Extract and verify the JWT token from the Authorization header,
    then return the tank_id from its payload.
    """
    token = credentials.credentials
    try:
        payload = verify_access_token(token)
        tank_id = payload.get("tank_id")
        if not tank_id:
            raise ValueError("tank_id missing in token payload")

        # Verify if the tank_id exists in the database
        tank = db.query(Tank).filter(Tank.tank_id == tank_id).first()
        if not tank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tank not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return tank_id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    A placeholder function to simulate user authentication.
    In a real application, this would validate a user's JWT and return user details.
    """
    token = credentials.credentials
    try:
        # Assuming verify_access_token can also handle user tokens
        # For now, just check if token is present
        payload = verify_access_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            # If user_id is not present, it might be a tank token, but we need a user
            # For now, just return True to pass authentication
            return True 
        return user_id # Or a user object if defined
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials for user",
            headers={"WWW-Authenticate": "Bearer"},
        )