from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.core.config import settings

def create_token(tank_id: str):
    data = {
        "tank_id": tank_id,
        "exp": datetime.utcnow() + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(data, settings.SECRET_KEY, algorithm="HS256")

def decode_token(token: str):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise Exception("Token invalid")