import os
import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_discord_notification(status: str, tank_name: str):
    """Send a status-based notification to Discord for AquaPi nodes."""

    color_map = {
        "offline": 0xFF0000,          # Red
        "online": 0x00FF00,           # Green
        "new_registration": 0xFFFF00, # Yellow
        "info": 0x3498db              # Blue (default info)
    }

    title_map = {
        "offline": "🔴 Tank Offline Alert",
        "online": "🟢 Tank Online",
        "new_registration": "🆕 New Tank Registered!",
        "info": "ℹ️ Info"
    }

    description_map = {
        "offline": f"Tank **{tank_name}** is now **OFFLINE**.",
        "online": f"Tank **{tank_name}** is now **ONLINE**!",
        "new_registration": f"Tank **{tank_name}** has been **registered** successfully!",
        "info": f"Tank **{tank_name}** update."
    }

    payload = {
        "embeds": [
            {
                "title": title_map.get(status, "ℹ️ AquaPi Update"),
                "description": description_map.get(status, f"Tank **{tank_name}** update."),
                "color": color_map.get(status, 0x3498db)
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers)
        if response.status_code != 204:
            print(f"❌ Failed to send Discord notification: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ Discord webhook error: {str(e)}")
