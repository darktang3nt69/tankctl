"""
Service for managing device push tokens and sending FCM notifications.
"""
import requests
import json
import google.auth
from google.oauth2 import service_account
from google.auth.transport.requests import Request

FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
FCM_ENDPOINT = "https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
from src.repository.device_push_token_repository import DevicePushTokenRepository
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

class PushNotificationService:
    def __init__(self, token_repository: DevicePushTokenRepository, service_account_path: str, project_id: str):
        self.token_repository = token_repository
        self.service_account_path = service_account_path
        self.project_id = project_id
        self._credentials = None

    def _get_access_token(self):
        if not self._credentials:
            self._credentials = service_account.Credentials.from_service_account_file(
                self.service_account_path, scopes=[FCM_SCOPE]
            )
        self._credentials.refresh(Request())
        return self._credentials.token

    def send_fcm_notification(self, token: str, title: str, body: str, data: dict = None) -> bool:
        """Send a push notification to a single device via FCM."""
        url = FCM_ENDPOINT.format(project_id=self.project_id)
        access_token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        message = {
            "message": {
                "token": token,
                "notification": {"title": title, "body": body},
                "data": data or {},
            }
        }
        try:
            resp = requests.post(url, headers=headers, json=message, timeout=5)
            if resp.status_code == 200:
                logger.info("fcm_sent", token=token, title=title)
                return True
            else:
                logger.error("fcm_failed", status=resp.status_code, response=resp.text[:200])
                return False
        except Exception as e:
            logger.error("fcm_error", error=str(e))
            return False

    def broadcast_fcm(self, device_id: str, title: str, body: str, data: dict = None) -> int:
        """Send a push notification to all tokens for a device."""
        tokens = self.token_repository.get_tokens_for_device(device_id)
        sent = 0
        for token in tokens:
            if self.send_fcm_notification(token, title, body, data):
                sent += 1
        return sent

    def upsert_device_token(self, device_id: str, token: str, platform: str) -> None:
        self.token_repository.upsert_token(device_id, token, platform)

    def remove_device_token(self, token: str) -> None:
        self.token_repository.remove_token(token)
