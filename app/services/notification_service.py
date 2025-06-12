from app.utils.discord import send_discord_embed, DISCORD_WEBHOOK_URL

class NotificationService:
    @staticmethod
    def is_configured():
        """
        Checks if the notification service (Discord) is configured.
        """
        return DISCORD_WEBHOOK_URL is not None

    @staticmethod
    def send_command_acknowledgement_notification(tank_name: str, command_payload: str, success: bool):
        """
        Sends a Discord embed notification when a tank acknowledges a command.
        """
        send_discord_embed(
            status="command_ack",
            tank_name=tank_name,
            command_payload=command_payload,
            success=success
        )

    @staticmethod
    def send_status_notification(status: str, tank_name: str, command_payload: str = None, success: bool = None, extra_fields: dict = None):
        """
        Sends a Discord embed notification for tank status updates (online, offline, retry, etc).
        """
        send_discord_embed(
            status=status,
            tank_name=tank_name,
            command_payload=command_payload,
            success=success,
            extra_fields=extra_fields
        )
