import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from app.utils.timezone import IST

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# -----------------------------------------
# Unified Discord Embed Notification
# -----------------------------------------
def send_discord_embed(status: str, tank_name: str, command_payload: str = None, success: bool = None, extra_fields: dict = None):
    """
    Send a styled embed notification to Discord for any AquaPi event.
    
    Args:
        status (str): One of: online, offline, new_registration, light_on, light_off, override_cleared, command_ack
        tank_name (str): Tank name shown in embed
        command_payload (str, optional): Used for command acknowledgment messages
        success (bool, optional): Used for command acknowledgment (success/failure)
        extra_fields (dict, optional): Any additional info to show
    """

    now_ist = datetime.now(IST)
    now_ist_iso = now_ist.isoformat()

    # 🎨 Material-inspired color palette
    color_map = {
        "offline": 0xB00020,
        "online": 0x00C853,
        "new_registration": 0xFFD600,
        "light_on": 0x00B0FF,
        "light_off": 0x1A237E,
        "override_cleared": 0x757575,
        "command_ack_success": 0x00FF00,
        "command_ack_fail": 0xFF0000,
        "info": 0x2962FF,
        "retry_scheduled": 0xF9A825,  # Material Amber 800
        "retry_failed": 0xD32F2F     # Material Red 700
    }

    # 🧱 Status config
    status_config = {
        "offline": {
            "emoji": "🔴",
            "title": "Tank Offline Alert",
            "description": f"Tank **{tank_name}** has not sent a heartbeat and is now **offline**.",
            "footer": "Marked offline at"
        },
        "online": {
            "emoji": "🟢",
            "title": "Tank Online",
            "description": f"Tank **{tank_name}** is now **online**.",
            "footer": "Marked online at"
        },
        "new_registration": {
            "emoji": "🆕",
            "title": "New Tank Registered",
            "description": f"Tank **{tank_name}** has been successfully registered.",
            "footer": "Registered at"
        },
        "light_on": {
            "emoji": "💡",
            "title": "Scheduled Light ON",
            "description": f"Tank **{tank_name}**: Lights turned **ON** by scheduled trigger.",
            "footer": "Light ON at"
        },
        "light_off": {
            "emoji": "🌙",
            "title": "Scheduled Lights OFF",
            "description": f"Tank **{tank_name}**: Lights turned **OFF** by scheduled trigger.",
            "footer": "Light OFF at"
        },
        "override_cleared": {
            "emoji": "🌀",
            "title": "Manual Override Cleared",
            "description": f"Tank **{tank_name}**: Manual override cleared. Schedule resumed.",
            "footer": "Override cleared at"
        },
        "command_ack": {
            "emoji": "✅" if success else "❌",
            "title": "Command Acknowledged" if success else "Command Failed",
            "description": f"Tank **{tank_name}** {'successfully' if success else 'failed to'} execute command `{command_payload}`.",
            "footer": "Acknowledged at"
        },
        "info": {
            "emoji": "ℹ️",
            "title": "Tank Update",
            "description": f"Tank **{tank_name}** has a status update.",
            "footer": "Update recorded at"
        },
        "manual_light_on": {
            "emoji": "🖐️",
            "title": "Manual Command: LIGHT ON",
            "description": f"Tank **{tank_name}**: Received manual command to turn **ON** the lights.",
            "footer": "Manual LIGHT ON issued at"
        },
        "manual_light_off": {
            "emoji": "✋",
            "title": "Manual Command: LIGHT OFF",
            "description": f"Tank **{tank_name}**: Received manual command to turn **OFF** the lights.",
            "footer": "Manual LIGHT OFF issued at"
        },
        "retry_scheduled": {
            "emoji": "🔁",
            "title": "Command Retry Scheduled",
            "description": f"Tank **{tank_name}**: Command retry has been scheduled.",
            "footer": "Next retry at"
        },
        "retry_failed": {
            "emoji": "💥",
            "title": "Command Retry Failed",
            "description": f"Tank **{tank_name}**: Command failed permanently after maximum retries.",
            "footer": "Marked failed at"
        },

    }

    # 🎯 Select final status (default to info)
    resolved_status = "command_ack" if status == "command_ack" else status
    config = status_config.get(resolved_status, status_config["info"])
    color = (
        color_map["command_ack_success"] if resolved_status == "command_ack" and success else
        color_map["command_ack_fail"] if resolved_status == "command_ack" else
        color_map.get(resolved_status, color_map["info"])
    )

    # 🛠️ Build embed
    embed = {
        "title": f"{config['emoji']} {config['title']}",
        "description": config["description"],
        "color": color,
        "timestamp": now_ist_iso,
        "footer": {
            "text": f"{config['footer']} {now_ist.strftime('%d %b %Y %I:%M %p IST')}"
        }
    }

    # ➕ Add extra fields
    if extra_fields:
        embed["fields"] = []
        for key, value in extra_fields.items():
            embed["fields"].append({
                "name": str(key),
                "value": str(value),
                "inline": True
            })

    # 📤 Send
    payload = {"embeds": [embed]}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers)
        if response.status_code not in [200, 204]:
            print(f"❌ Failed to send Discord embed: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ Discord webhook error: {str(e)}")
