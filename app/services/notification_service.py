# app/services/notification_service.py

from app.utils.discord import send_command_acknowledgement_embed, send_status_embed_notification

class NotificationService:
    @staticmethod
    def send_command_acknowledgement_notification(tank_name: str, command_payload: str, success: bool):
        """
        Sends a Discord embed notification when a tank acknowledges a command.
        """
        send_command_acknowledgement_embed(tank_name, command_payload, success)

    @staticmethod
    def send_status_notification(status: str, tank_name: str):
        """
        Sends a Discord embed notification for tank status updates (online/offline/registration).
        """
        send_status_embed_notification(status, tank_name)
