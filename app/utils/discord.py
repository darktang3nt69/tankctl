import os
import httpx # Use httpx for async requests
from datetime import datetime
from dotenv import load_dotenv
from app.utils.timezone import IST

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# -----------------------------------------
# Unified Discord Embed Notification
# -----------------------------------------
async def send_discord_embed(status: str, tank_name: str, command_payload: str = None, success: bool = None, extra_fields: dict = None):
    """
    Send a styled embed notification to Discord for any AquaPi event asynchronously.
    
    Args:
        status (str): One of: online, offline, new_registration, light_on, light_off,
                      override_cleared, manual_light_on, manual_light_off, command_ack, info, retry_scheduled, retry_failed
        tank_name (str): Tank name shown in embed
        command_payload (str, optional): Used for command acknowledgment messages
        success (bool, optional): Used for command acknowledgment (success/failure)
        extra_fields (dict, optional): Any additional info to show
    """

    if not DISCORD_WEBHOOK_URL:
        print("DEBUG: DISCORD_WEBHOOK_URL not set. Skipping Discord notification.")
        return

    now_ist = datetime.now(IST)
    now_ist_iso = now_ist.isoformat()

    # 🎨 Material-inspired color palette
    color_map = {
        "offline":            0xB00020,   # Red 800
        "online":             0x00C853,   # Green A700
        "new_registration":   0xFFD600,   # Yellow A400
        "light_on":           0x00B0FF,   # Light Blue A400
        "light_off":          0x1A237E,   # Indigo 900
        "override_cleared":   0x757575,   # Grey 600
        "manual_light_on":    0x8E24AA,   # Deep Purple 600
        "manual_light_off":   0xD81B60,   # Pink 600
        "command_ack_success":0x00E676,   # Green A400
        "command_ack_fail":   0xFF1744,   # Red A400
        "info":               0x2962FF,   # Blue 800
        "retry_scheduled":    0xF9A825,   # Amber 800
        "retry_failed":       0xD32F2F    # Red 700
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
        "manual_light_on": {
            "emoji": "🖐️",
            "title": "Manual Command: LIGHT ON",
            "description": f"Tank **{tank_name}**: Lights **FORCED ON** by manual override.",
            "footer": "Manual LIGHT ON at"
        },
        "manual_light_off": {
            "emoji": "✋",
            "title": "Manual Command: LIGHT OFF",
            "description": f"Tank **{tank_name}**: Lights **FORCED OFF** by manual override.",
            "footer": "Manual LIGHT OFF at"
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

    # 🎯 Choose final status config (default to info)
    config = status_config.get(status, status_config["info"])
    color = color_map.get(status, color_map["info"])

    # 🛠️ Build embed
    embed = {
        "title":       f"{config['emoji']} {config['title']}",
        "description": config["description"],
        "color":       color,
        "timestamp":   now_ist_iso,
        "footer": {
            "text": f"{config['footer']} {now_ist.strftime('%d %b %Y %I:%M %p IST')}"
        }
    }

    # ➕ Add extra fields
    if extra_fields:
        embed["fields"] = []
        for key, value in extra_fields.items():
            embed["fields"].append({
                "name":  str(key),
                "value": str(value),
                "inline": True
            })

    # 📤 Send
    # Refer to Discord Webhook documentation for payload structure: https://discord.com/developers/docs/resources/webhook
    payload = {"embeds": [embed]}
    headers = {"Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers)
            if resp.status_code not in (200, 204):
                print(f"❌ Failed to send Discord embed: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"❌ Discord webhook error: {e}")
