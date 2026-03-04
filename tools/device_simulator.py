#!/usr/bin/env python3
"""
TankCtl Device Simulator

Simulates multiple IoT devices communicating with the TankCtl backend via MQTT.

Each device:
- Connects to the MQTT broker
- Subscribes to command topics
- Publishes telemetry (every 5 seconds)
- Publishes heartbeat (every 30 seconds)
- Handles commands and reports state changes

Usage:
    python tools/device_simulator.py --devices 10 --broker localhost --port 1883
    python tools/device_simulator.py --devices 50
    python tools/device_simulator.py --help

Architecture:
    DeviceSimulator (orchestrator)
        ├── SimulatedDevice (tank1)
        ├── SimulatedDevice (tank2)
        └── SimulatedDevice (tank3)
        ...
"""

import asyncio
import json
import logging
import random
import sys
from argparse import ArgumentParser
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

import paho.mqtt.client as mqtt


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("simulator")


@dataclass
class DeviceState:
    """Internal state of a simulated device."""

    light: str = "off"  # on/off
    pump: str = "off"  # on/off
    temperature: float = 22.0  # °C
    humidity: float = 55.0  # %
    pressure: float = 1013.25  # hPa
    last_command_version: int = 0  # For idempotency


class SimulatedDevice:
    """Simulates a single IoT device communicating via MQTT."""

    def __init__(
        self,
        device_id: str,
        device_secret: str,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        username: str = "tankctl",
        password: str = "password",
    ):
        """Initialize a simulated device.

        Args:
            device_id: Unique device identifier (e.g., 'tank1')
            device_secret: Device authentication secret
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port
            username: MQTT broker username
            password: MQTT broker password
        """
        self.device_id = device_id
        self.device_secret = device_secret
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.mqtt_username = username
        self.mqtt_password = password

        # Internal device state
        self.state = DeviceState()

        # MQTT client
        self.client: Optional[mqtt.Client] = None
        self.connected = False

        # Task management
        self._tasks: list = []
        self._running = False

        # Telemetry simulation
        self.temp_trend = random.uniform(-0.5, 0.5)  # Trend per measurement

    def _setup_mqtt_client(self) -> mqtt.Client:
        """Create and configure MQTT client.

        Returns:
            Configured MQTT client
        """
        client_id = f"tankctl-device-{self.device_id}"
        client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)

        # Set credentials
        client.username_pw_set(self.mqtt_username, self.mqtt_password)

        # Set callbacks
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        client.on_publish = self._on_publish

        return client

    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection."""
        if rc == 0:
            self.connected = True
            logger.info(
                f"[{self.device_id}] mqtt_connected broker={self.broker_host}:{self.broker_port}"
            )

            # Subscribe to command topic
            command_topic = f"tankctl/{self.device_id}/command"
            client.subscribe(command_topic, qos=1)
            logger.debug(f"[{self.device_id}] subscribed_to topic={command_topic}")
        else:
            logger.error(f"[{self.device_id}] mqtt_connection_failed rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection."""
        self.connected = False
        if rc != 0:
            logger.warning(
                f"[{self.device_id}] mqtt_disconnected_unexpectedly rc={rc}"
            )
        else:
            logger.info(f"[{self.device_id}] mqtt_disconnected rc={rc}")

    def _on_publish(self, client, userdata, mid):
        """Handle MQTT publish confirmation."""
        pass  # Silent - too verbose for logging

    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT message (command)."""
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            logger.info(
                f"[{self.device_id}] command_received command={payload.get('command')} "
                f"value={payload.get('value')} version={payload.get('version')}"
            )

            # Extract command details
            command = payload.get("command")
            value = payload.get("value")
            version = payload.get("version", 0)

            # Check idempotency: ignore if we've already processed this command version
            if version <= self.state.last_command_version:
                logger.debug(
                    f"[{self.device_id}] ignoring_stale_command version={version} "
                    f"current={self.state.last_command_version}"
                )
                return

            # Update state based on command
            if command == "set_light":
                self.state.light = value
                self.state.last_command_version = version
                logger.info(f"[{self.device_id}] state_updated light={self.state.light}")

            elif command == "set_pump":
                self.state.pump = value
                self.state.last_command_version = version
                logger.info(f"[{self.device_id}] state_updated pump={self.state.pump}")

            # Publish reported state
            asyncio.create_task(self._publish_reported_state())

        except json.JSONDecodeError as e:
            logger.error(f"[{self.device_id}] invalid_json_command error={str(e)}")
        except Exception as e:
            logger.error(f"[{self.device_id}] command_processing_error error={str(e)}")

    async def _publish_reported_state(self) -> None:
        """Publish device's current state to reported topic."""
        if not self.connected or self.client is None:
            return

        topic = f"tankctl/{self.device_id}/reported"
        payload = json.dumps(
            {"light": self.state.light, "pump": self.state.pump},
            separators=(",", ":"),
        )

        try:
            self.client.publish(topic, payload, qos=1, retain=True)
            logger.debug(f"[{self.device_id}] reported_state_published light={self.state.light} pump={self.state.pump}")
        except Exception as e:
            logger.error(f"[{self.device_id}] publish_error topic={topic} error={str(e)}")

    async def _publish_telemetry(self) -> None:
        """Publish telemetry data every 5 seconds."""
        while self._running:
            if not self.connected or self.client is None:
                await asyncio.sleep(1)
                continue

            try:
                # Simulate temperature variation
                self.state.temperature += self.temp_trend
                self.state.temperature += random.uniform(-0.2, 0.2)  # Small noise

                # Constrain to reasonable range
                self.state.temperature = max(10.0, min(40.0, self.state.temperature))

                # Simulate humidity variation
                self.state.humidity += random.uniform(-2, 2)
                self.state.humidity = max(30.0, min(90.0, self.state.humidity))

                # Publish telemetry
                topic = f"tankctl/{self.device_id}/telemetry"
                payload = json.dumps(
                    {
                        "temperature": round(self.state.temperature, 2),
                        "humidity": round(self.state.humidity, 2),
                        "pressure": round(self.state.pressure, 2),
                    },
                    separators=(",", ":"),
                )

                self.client.publish(topic, payload, qos=0, retain=False)
                logger.debug(
                    f"[{self.device_id}] telemetry temperature={self.state.temperature:.1f}°C "
                    f"humidity={self.state.humidity:.1f}% pressure={self.state.pressure:.2f}hPa"
                )

            except Exception as e:
                logger.error(f"[{self.device_id}] telemetry_publish_error error={str(e)}")

            await asyncio.sleep(5)  # Publish every 5 seconds

    async def _publish_heartbeat(self) -> None:
        """Publish heartbeat message every 30 seconds."""
        uptime_seconds = 0

        while self._running:
            if not self.connected or self.client is None:
                await asyncio.sleep(1)
                continue

            try:
                topic = f"tankctl/{self.device_id}/heartbeat"
                payload = json.dumps(
                    {
                        "status": "online",
                        "uptime": uptime_seconds,
                    },
                    separators=(",", ":"),
                )

                self.client.publish(topic, payload, qos=0, retain=False)
                logger.debug(
                    f"[{self.device_id}] heartbeat_published status=online uptime={uptime_seconds}s"
                )
                uptime_seconds += 30

            except Exception as e:
                logger.error(f"[{self.device_id}] heartbeat_publish_error error={str(e)}")

            await asyncio.sleep(30)  # Publish every 30 seconds

    async def connect(self) -> bool:
        """Connect to MQTT broker.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = self._setup_mqtt_client()
            logger.info(
                f"[{self.device_id}] mqtt_connecting broker={self.broker_host}:{self.broker_port}"
            )
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)

            # Start network loop in a thread
            self.client.loop_start()

            # Wait for connection
            max_retries = 10
            for attempt in range(max_retries):
                if self.connected:
                    return True
                await asyncio.sleep(0.5)

            logger.error(f"[{self.device_id}] mqtt_connection_timeout")
            return False

        except Exception as e:
            logger.error(f"[{self.device_id}] mqtt_connection_error error={str(e)}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self.client is not None:
            try:
                self._running = False
                self.client.loop_stop()
                self.client.disconnect()
                logger.info(f"[{self.device_id}] mqtt_disconnected")
            except Exception as e:
                logger.error(f"[{self.device_id}] mqtt_disconnect_error error={str(e)}")

    async def start(self) -> None:
        """Start the device (connect and run tasks)."""
        if not await self.connect():
            logger.error(f"[{self.device_id}] failed_to_connect, aborting")
            return

        # Publish initial reported state
        await self._publish_reported_state()
        await asyncio.sleep(1)

        # Start background tasks
        self._running = True
        telemetry_task = asyncio.create_task(self._publish_telemetry())
        heartbeat_task = asyncio.create_task(self._publish_heartbeat())
        self._tasks = [telemetry_task, heartbeat_task]

        logger.info(f"[{self.device_id}] device_started")

        try:
            # Run until cancelled
            await asyncio.gather(*self._tasks)
        except asyncio.CancelledError:
            logger.info(f"[{self.device_id}] device_stopped")
            raise

    async def stop(self) -> None:
        """Stop the device and cancel tasks."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        await self.disconnect()


class DeviceSimulator:
    """Orchestrates multiple simulated devices."""

    def __init__(
        self,
        device_count: int = 10,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        mqtt_username: str = "tankctl",
        mqtt_password: str = "password",
    ):
        """Initialize device simulator.

        Args:
            device_count: Number of devices to simulate
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port
            mqtt_username: MQTT broker username
            mqtt_password: MQTT broker password
        """
        self.device_count = device_count
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.mqtt_username = mqtt_username
        self.mqtt_password = mqtt_password
        self.devices: Dict[str, SimulatedDevice] = {}
        self._tasks: list = []

    async def _create_devices(self) -> None:
        """Create simulated devices."""
        logger.info(f"Creating {self.device_count} simulated devices...")

        for i in range(1, self.device_count + 1):
            device_id = f"tank{i}"
            device_secret = f"secret_{device_id}"

            device = SimulatedDevice(
                device_id=device_id,
                device_secret=device_secret,
                broker_host=self.broker_host,
                broker_port=self.broker_port,
                username=self.mqtt_username,
                password=self.mqtt_password,
            )

            self.devices[device_id] = device
            logger.debug(f"Created device: {device_id}")

            # Stagger device connections to avoid thunder herd
            await asyncio.sleep(0.2)

    async def _start_all_devices(self) -> None:
        """Start all devices concurrently."""
        logger.info(f"Starting {self.device_count} devices...")

        self._tasks = [
            asyncio.create_task(device.start())
            for device in self.devices.values()
        ]

        try:
            await asyncio.gather(*self._tasks)
        except asyncio.CancelledError:
            logger.info("Device simulation cancelled")
            raise

    async def run(self) -> None:
        """Run the device simulator."""
        try:
            # Create devices
            await self._create_devices()
            logger.info(f"✓ Created {self.device_count} devices")

            # Print device list
            logger.info("Device IDs:")
            for device_id in sorted(self.devices.keys()):
                logger.info(f"  - {device_id}")

            # Start all devices
            await self._start_all_devices()

        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        except Exception as e:
            logger.error(f"Simulator error: {str(e)}", exc_info=True)
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop all devices."""
        logger.info("Stopping all devices...")

        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)

        # Disconnect all devices
        tasks = [device.stop() for device in self.devices.values()]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("✓ All devices stopped")


async def main():
    """Main entry point."""
    parser = ArgumentParser(description="TankCtl Device Simulator")
    parser.add_argument(
        "--devices",
        type=int,
        default=10,
        help="Number of devices to simulate (default: 10)",
    )
    parser.add_argument(
        "--broker",
        type=str,
        default="localhost",
        help="MQTT broker hostname (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=1883,
        help="MQTT broker port (default: 1883)",
    )
    parser.add_argument(
        "--username",
        type=str,
        default="tankctl",
        help="MQTT broker username (default: tankctl)",
    )
    parser.add_argument(
        "--password",
        type=str,
        default="password",
        help="MQTT broker password (default: password)",
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("TankCtl Device Simulator")
    logger.info("=" * 60)
    logger.info(f"Devices: {args.devices}")
    logger.info(f"Broker: {args.broker}:{args.port}")
    logger.info(f"Username: {args.username}")
    logger.info("=" * 60)

    simulator = DeviceSimulator(
        device_count=args.devices,
        broker_host=args.broker,
        broker_port=args.port,
        mqtt_username=args.username,
        mqtt_password=args.password,
    )

    try:
        await simulator.run()
    except KeyboardInterrupt:
        logger.info("Caught KeyboardInterrupt, exiting...")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
