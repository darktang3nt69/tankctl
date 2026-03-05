#!/usr/bin/env python3
"""
Shadow Reconciliation Demo

Demonstrates:
1. Multiple devices (3 devices)
2. Setting desired state while devices are offline
3. Reconciliation sending commands
4. Devices coming online and executing commands
5. Shadow synchronization

Usage:
    python tools/reconciliation_demo.py
"""

import asyncio
import sys
import time
from datetime import datetime
from typing import Dict, List

import requests

# Add parent directory to path for imports
sys.path.insert(0, "/home/lokesh/tankctl")
from tools.device_simulator import DeviceSimulator


class ReconciliationDemo:
    """Demonstrate shadow reconciliation with multiple devices."""

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        broker_host: str = "localhost",
        broker_port: int = 1883,
    ):
        self.api_url = api_url
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.device_ids = ["tank1", "tank2", "tank3"]
        self.simulator = None

    def log(self, msg: str, level: str = "INFO"):
        """Print timestamped log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level:5} - {msg}")

    def register_devices(self):
        """Register all devices via API."""
        self.log("=" * 70)
        self.log("STEP 1: Register Devices")
        self.log("=" * 70)

        for device_id in self.device_ids:
            try:
                response = requests.post(
                    f"{self.api_url}/devices",
                    json={"device_id": device_id, "device_secret": f"secret_{device_id}"},
                    timeout=5,
                )
                if response.status_code in [200, 201]:
                    self.log(f"✓ Registered: {device_id}")
                elif response.status_code == 409:
                    self.log(f"✓ Already exists: {device_id}")
                else:
                    self.log(f"✗ Failed to register: {device_id}", "ERROR")
            except Exception as e:
                self.log(f"✗ Error registering {device_id}: {e}", "ERROR")

        time.sleep(1)

    def get_shadow_state(self, device_id: str) -> Dict:
        """Get device shadow state."""
        try:
            response = requests.get(f"{self.api_url}/devices/{device_id}/shadow", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.log(f"Error getting shadow for {device_id}: {e}", "ERROR")
        return {}

    def set_desired_state_offline(self):
        """Set desired state while devices are offline."""
        self.log("")
        self.log("=" * 70)
        self.log("STEP 2: Set Desired State (Devices OFFLINE)")
        self.log("=" * 70)

        desired_states = {
            self.device_ids[0]: {"light": "on", "pump": "off"},
            self.device_ids[1]: {"light": "off", "pump": "on"},
            self.device_ids[2]: {"light": "on", "pump": "on"},
        }

        for device_id, desired in desired_states.items():
            try:
                # Get current shadow
                shadow = self.get_shadow_state(device_id)
                reported = shadow.get("reported", {})

                self.log(f"{device_id}:")
                self.log(f"  Current reported: {reported}")
                self.log(f"  Setting desired:  {desired}")

                # Update desired state
                response = requests.put(
                    f"{self.api_url}/devices/{device_id}/shadow",
                    json={"desired": desired},
                    timeout=5,
                )

                if response.status_code == 200:
                    updated = response.json()
                    self.log(f"  ✓ Shadow updated (version: {updated.get('version')})")
                    self.log(f"  Synchronized: {updated.get('synchronized')}")
                else:
                    self.log(f"  ✗ Failed to update shadow", "ERROR")

            except Exception as e:
                self.log(f"✗ Error updating {device_id}: {e}", "ERROR")

        time.sleep(2)

    def check_reconciliation_commands(self):
        """Check if reconciliation created commands."""
        self.log("")
        self.log("=" * 70)
        self.log("STEP 3: Wait for Scheduler Reconciliation")
        self.log("=" * 70)
        self.log("Waiting 12 seconds for scheduler to detect drift and send commands...")

        time.sleep(12)

        self.log("")
        self.log("Checking command history:")

        for device_id in self.device_ids:
            try:
                response = requests.get(
                    f"{self.api_url}/devices/{device_id}/commands?limit=10",
                    timeout=5,
                )
                if response.status_code == 200:
                    data = response.json()
                    commands = data.get("commands", [])
                    recent = [c for c in commands if c.get("status") in ["pending", "sent"]]

                    self.log(f"{device_id}: {len(recent)} pending/sent commands")
                    for cmd in recent[:3]:
                        self.log(
                            f"  - {cmd.get('command')} = {cmd.get('value')} "
                            f"(v{cmd.get('version')}, {cmd.get('status')})"
                        )
            except Exception as e:
                self.log(f"Error checking commands for {device_id}: {e}", "ERROR")

        time.sleep(2)

    async def start_devices_and_execute(self):
        """Start devices and let them execute commands."""
        self.log("")
        self.log("=" * 70)
        self.log("STEP 4: Start Devices (Going ONLINE)")
        self.log("=" * 70)

        # Create simulator with 3 devices
        self.simulator = DeviceSimulator(
            device_count=3,
            broker_host=self.broker_host,
            broker_port=self.broker_port,
            mqtt_username="tankctl",
            mqtt_password="password",
        )

        self.log("Starting device simulator...")

        # Start simulator in background
        simulator_task = asyncio.create_task(self.simulator.run())

        # Wait for devices to connect and process commands
        self.log("Waiting 10 seconds for devices to connect and execute commands...")
        await asyncio.sleep(10)

        # Check final state
        self.log("")
        self.log("=" * 70)
        self.log("STEP 5: Verify Shadow Synchronization")
        self.log("=" * 70)

        for device_id in self.device_ids:
            shadow = self.get_shadow_state(device_id)
            if shadow:
                desired = shadow.get("desired", {})
                reported = shadow.get("reported", {})
                synchronized = shadow.get("synchronized", False)

                self.log(f"{device_id}:")
                self.log(f"  Desired:       {desired}")
                self.log(f"  Reported:      {reported}")
                self.log(f"  Synchronized:  {'✓' if synchronized else '✗'}")

        # Stop simulator
        self.log("")
        self.log("Stopping devices...")
        simulator_task.cancel()
        await asyncio.sleep(2)

    async def run(self):
        """Run the complete demo."""
        try:
            self.log("=" * 70)
            self.log("TankCtl Shadow Reconciliation Demo")
            self.log("=" * 70)
            self.log("")

            # Step 1: Register devices
            self.register_devices()

            # Step 2: Set desired state (devices offline)
            self.set_desired_state_offline()

            # Step 3: Wait for reconciliation
            self.check_reconciliation_commands()

            # Step 4 & 5: Start devices and verify
            await self.start_devices_and_execute()

            self.log("")
            self.log("=" * 70)
            self.log("Demo Complete!")
            self.log("=" * 70)
            self.log("")
            self.log("What happened:")
            self.log("1. 3 devices registered (offline)")
            self.log("2. Desired state set via API (light/pump states)")
            self.log("3. Scheduler detected drift and sent reconciliation commands")
            self.log("4. Devices came online and received commands via MQTT")
            self.log("5. Devices executed commands and reported new state")
            self.log("6. Shadows synchronized (desired = reported)")

        except KeyboardInterrupt:
            self.log("Demo interrupted", "WARN")
        except Exception as e:
            self.log(f"Demo error: {e}", "ERROR")
            raise
        finally:
            if self.simulator:
                self.log("Cleaning up simulator...")


async def main():
    """Main entry point."""
    demo = ReconciliationDemo()
    await demo.run()


if __name__ == "__main__":
    asyncio.run(main())
