"""
MQTT client for TankCtl backend.

Handles connection to Mosquitto broker, subscriptions, and message routing.
"""

import json
from abc import ABC, abstractmethod
from typing import Callable

import paho.mqtt.client as mqtt

from src.config.settings import settings
from src.infrastructure.mqtt.mqtt_topics import MQTTTopics
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MessageHandler(ABC):
    """Base class for MQTT message handlers."""

    @abstractmethod
    def handle(self, device_id: str, payload: dict) -> None:
        """Handle incoming message."""
        pass


class MQTTClient:
    """MQTT client for TankCtl backend."""

    def __init__(self) -> None:
        """Initialize MQTT client."""
        self.client = mqtt.Client()
        self.handlers: dict[str, list[MessageHandler]] = {}
        self.is_connected = False

        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe

    def register_handler(self, channel: str, handler: MessageHandler) -> None:
        """
        Register a message handler for a specific channel.

        Args:
            channel: MQTT channel (telemetry, reported, heartbeat, command)
            handler: MessageHandler instance
        """
        if channel not in self.handlers:
            self.handlers[channel] = []
        self.handlers[channel].append(handler)
        logger.debug(f"Registered handler for channel: {channel}")

    def connect(self) -> None:
        """Connect to MQTT broker."""
        logger.info(
            "mqtt_connecting",
            broker_host=settings.mqtt.broker_host,
            broker_port=settings.mqtt.broker_port,
        )

        try:
            if settings.mqtt.username and settings.mqtt.password:
                self.client.username_pw_set(settings.mqtt.username, settings.mqtt.password)

            self.client.connect(
                settings.mqtt.broker_host,
                settings.mqtt.broker_port,
                settings.mqtt.keepalive,
            )
            self.client.loop_start()
            logger.info("mqtt_connected")
        except Exception as e:
            logger.error("mqtt_connection_failed", error=str(e))
            raise

    def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        logger.info("mqtt_disconnecting")
        self.client.loop_stop()
        self.client.disconnect()
        self.is_connected = False

    def subscribe(self) -> None:
        """Subscribe to backend topics."""
        topics_to_subscribe = [
            MQTTTopics.SUBSCRIBE_TELEMETRY,
            MQTTTopics.SUBSCRIBE_REPORTED,
            MQTTTopics.SUBSCRIBE_HEARTBEAT,
            MQTTTopics.SUBSCRIBE_STATUS,
        ]

        for topic in topics_to_subscribe:
            self.client.subscribe(topic, qos=settings.mqtt.qos)
            logger.debug("mqtt_subscribed", topic=topic)

    def publish(
        self,
        topic: str,
        payload: dict,
        qos: int | None = None,
        retain: bool = False,
    ) -> None:
        """
        Publish message to MQTT topic.

        Args:
            topic: MQTT topic
            payload: Message payload (will be JSON encoded)
            qos: Quality of Service (0, 1, or 2)
            retain: Whether to retain the message
        """
        if qos is None:
            qos = settings.mqtt.qos

        message = json.dumps(payload)

        try:
            result = self.client.publish(topic, message, qos=qos, retain=retain)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(
                    "mqtt_publish_failed",
                    topic=topic,
                    error_code=result.rc,
                )
            else:
                logger.debug("mqtt_published", topic=topic)
        except Exception as e:
            logger.error("mqtt_publish_error", topic=topic, error=str(e))
            raise

    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback (paho-mqtt 1.x)."""
        if rc == 0:
            self.is_connected = True
            logger.info("mqtt_on_connect_success")
            self.subscribe()
        else:
            logger.error("mqtt_on_connect_failed", reason_code=rc)

    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback (paho-mqtt 1.x)."""
        self.is_connected = False
        if rc != 0:
            logger.warning("mqtt_unexpected_disconnect", reason_code=rc)
        else:
            logger.info("mqtt_disconnected")

    def _on_message(self, client, userdata, msg):
        """MQTT message callback."""
        try:
            topic = msg.topic
            payload_str = msg.payload.decode("utf-8")
            payload = json.loads(payload_str)

            device_id = MQTTTopics.extract_device_id(topic)
            channel = MQTTTopics.extract_channel(topic)

            if not device_id or not channel:
                logger.warning("mqtt_invalid_topic", topic=topic)
                return

            logger.debug(
                "mqtt_message_received",
                device_id=device_id,
                channel=channel,
            )

            # Route to handlers
            if channel in self.handlers:
                for handler in self.handlers[channel]:
                    try:
                        handler.handle(device_id, payload)
                    except Exception as e:
                        logger.error(
                            "mqtt_handler_error",
                            device_id=device_id,
                            channel=channel,
                            error=str(e),
                        )
        except json.JSONDecodeError as e:
            logger.error("mqtt_json_decode_error", error=str(e))
        except Exception as e:
            logger.error("mqtt_message_error", error=str(e))

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """MQTT subscribe callback (paho-mqtt 1.x)."""
        logger.debug("mqtt_subscribe_success", mid=mid, granted_qos=str(granted_qos))


# Singleton instance
mqtt_client = MQTTClient()
