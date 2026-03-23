"""
Repository for device push tokens (FCM, etc).
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from src.infrastructure.db.models import DevicePushTokenModel

class DevicePushTokenRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert_token(self, device_id: str, token: str, platform: str) -> None:
        obj = self.session.query(DevicePushTokenModel).filter_by(token=token).first()
        now = datetime.utcnow()
        if obj:
            obj.device_id = device_id
            obj.platform = platform
            obj.last_seen = now
        else:
            obj = DevicePushTokenModel(
                device_id=device_id,
                token=token,
                platform=platform,
                last_seen=now,
            )
            self.session.add(obj)
        self.session.commit()

    def get_tokens_for_device(self, device_id: str) -> list[str]:
        return [row.token for row in self.session.query(DevicePushTokenModel).filter_by(device_id=device_id).all()]

    def remove_token(self, token: str) -> None:
        obj = self.session.query(DevicePushTokenModel).filter_by(token=token).first()
        if obj:
            self.session.delete(obj)
            self.session.commit()

    def get_all_tokens(self) -> list[str]:
        return [row.token for row in self.session.query(DevicePushTokenModel).all()]
