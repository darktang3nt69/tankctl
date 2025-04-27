import requests
from app.core.config import settings

def send_discord_notification(message: str):
    """
    Sends a simple message to the Discord webhook.
    """
    if not settings.DISCORD_WEBHOOK_URL:
        print("[Discord] Webhook URL not configured.")
        return

    data = {
        "content": message
    }

    try:
        response = requests.post(settings.DISCORD_WEBHOOK_URL, json=data)
        if response.status_code == 204:
            print("[Discord] Notification sent successfully.")
        else:
            print(f"[Discord] Failed to send notification: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[Discord] Error sending notification: {str(e)}")
