# app/utils/discord.py

import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from app.utils.timezone import IST

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_discord_notification(status: str, tank_name: str):
    """
    Send a styled embed notification to Discord for AquaPi tanks.
    Includes timestamp and status color coding.
    """

    color_map = {
        "offline": 0xFF0000,          # Red
        "online": 0x00FF00,           # Green
        "new_registration": 0xFFFF00, # Yellow
        "info": 0x3498db              # Blue (default)
    }

    title_map = {
        "offline": "🔴 Tank Offline Alert",
        "online": "🟢 Tank Online",
        "new_registration": "🆕 New Tank Registered",
        "info": "ℹ️ Info"
    }

    description_map = {
        "offline": f"Tank **{tank_name}** is now **OFFLINE**.",
        "online": f"Tank **{tank_name}** is now **ONLINE**!",
        "new_registration": f"Tank **{tank_name}** has been **registered successfully!**",
        "info": f"Tank **{tank_name}** update."
    }

    footer_map = {
        "offline": "Device marked offline at",
        "online": "Device marked online at",
        "new_registration": "Device registered at",
        "info": "Update recorded at"
    }

    now_ist = datetime.now(IST)
    now_ist_iso = now_ist.isoformat()

    payload = {
        "embeds": [
            {
                "title": title_map.get(status, "ℹ️ AquaPi Update"),
                "description": description_map.get(status, f"Tank **{tank_name}** update."),
                "color": color_map.get(status, 0x3498db),
                "timestamp": now_ist_iso,  # 🕰️ ISO timestamp inside embed!
                "footer": {
                    "text": f"{footer_map.get(status, 'Update recorded at')} {now_ist.strftime('%d %b %Y %I:%M %p IST')}"
                }
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers)
        if response.status_code not in [200, 204]:
            print(f"❌ Failed to send Discord notification: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ Discord webhook error: {str(e)}")
