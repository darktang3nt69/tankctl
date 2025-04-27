import os
from datetime import datetime, timedelta

import jwt
from jwt import PyJWTError
from fastapi import HTTPException, status

from app.core.config import settings


def create_jwt_token(tank_id: str) -> str:
    """
    Create a signed JWT including the tank_id and expiration.
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": "tank",
        "tank_id": tank_id,
        "exp": expire
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_access_token(token: str) -> dict:
    """
    Decode and validate a JWT, returning its payload or raising an HTTPException if invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if "tank_id" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        return payload

    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token"
        )
