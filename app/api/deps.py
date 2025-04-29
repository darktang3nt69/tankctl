from typing import Generator

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.utils.jwt import verify_access_token

from app.core.config import settings

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
    credentials: HTTPAuthorizationCredentials = Depends(security)
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
        return tank_id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_admin_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid Admin API Key")