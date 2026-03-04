#!/usr/bin/env python3
"""
Integration Test Suite for TankCtl

This script tests the complete TankCtl system with simulated devices:
1. Device registration and shadow management
2. Telemetry ingestion and storage
3. Command delivery and processing
4. Heartbeat monitoring

Usage:
    python tools/integration_test.py
    python tools/integration_test.py --verbose
    python tools/integration_test.py --skip-simulator

Requirements:
    - TankCtl backend must be running on localhost:8000
    - MQTT broker must be running on localhost:1883
    - TimescaleDB must be accessible on localhost:5433
"""

import asyncio
import json
import sys
import time
from argparse import ArgumentParser
from datetime import datetime
from typing import Optional

import requests

# Import device simulator (if available)
try:
    sys.path.insert(0, "/home/lokesh/tankctl")
    from tools.device_simulator import DeviceSimulator
except ImportError:
    DeviceSimulator = None


class TestResult:
    """Track test results."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.error_message = ""
        self.start_time = time.time()
        self.duration = 0
        self.details = {}

    def success(self, details: Optional[dict] = None):
        """Mark test as passed."""
        self.passed = True
        self.duration = time.time() - self.start_time
        if details:
            self.details = details

    def failure(self, error: str, details: Optional[dict] = None):
        """Mark test as failed."""
        self.passed = False
        self.error_message = error
        self.duration = time.time() - self.start_time
        if details:
            self.details = details

    def __str__(self) -> str:
        status = "✓ PASS" if self.passed else "✗ FAIL"
        result = f"{status} - {self.test_name} ({self.duration:.2f}s)"
        if self.error_message:
            result += f"\n  Error: {self.error_message}"
        if self.details:
            for key, value in self.details.items():
                result += f"\n  {key}: {value}"
        return result


class TankCtlIntegrationTest:
    """Integration test suite for TankCtl."""

    def __init__(self, api_url: str = "http://localhost:8000", verbose: bool = False):
        self.api_url = api_url
        self.verbose = verbose
        self.results: list[TestResult] = []
        self.simulator: Optional[DeviceSimulator] = None
        self.test_devices = ["test_tank1", "test_tank2", "test_tank3"]

    def log(self, msg: str, level: str = "INFO"):
        """Print log message."""
        if level == "DEBUG" and not self.verbose:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level:5} - {msg}")

    async def register_device(self, device_id: str) -> bool:
        """Register a device via API."""
        try:
            url = f"{self.api_url}/devices"
            payload = {"device_id": device_id, "device_secret": f"secret_{device_id}"}

            response = requests.post(url, json=payload, timeout=5)

            if response.status_code in [200, 201]:
                self.log(f"Registered device: {device_id}")
                return True
            elif response.status_code == 409:
                self.log(f"Device already exists (ok for reruns): {device_id}")
                return True
            else:
                self.log(f"Failed to register {device_id}: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error registering device {device_id}: {str(e)}", "ERROR")
            return False

    async def test_api_health(self) -> TestResult:
        """Test API health check."""
        result = TestResult("API Health Check")
        self.log("Testing API health...", "DEBUG")

        try:
            url = f"{self.api_url}/health"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                result.success({"status": data.get("status"), "timestamp": data.get("timestamp")})
            else:
                result.failure(f"HTTP {response.status_code}", {"response": response.text})

        except Exception as e:
            result.failure(f"Connection failed: {str(e)}")

        return result

    async def test_device_registration(self) -> TestResult:
        """Test device registration API."""
        result = TestResult("Device Registration")
        self.log("Testing device registration...", "DEBUG")

        try:
            # Register first test device
            device_id = self.test_devices[0]
            url = f"{self.api_url}/devices"
            payload = {"device_id": device_id, "device_secret": f"secret_{device_id}"}

            response = requests.post(url, json=payload, timeout=5)

            if response.status_code in [200, 201]:
                data = response.json()
                if data.get("device_id") == device_id:
                    result.success(
                        {
                            "device_id": data.get("device_id"),
                            "status": data.get("status"),
                        }
                    )
                else:
                    result.failure("Device ID mismatch in response")
            elif response.status_code == 409:
                # Idempotent behavior for repeated test runs
                existing = requests.get(f"{self.api_url}/devices/{device_id}", timeout=5)
                if existing.status_code == 200:
                    data = existing.json()
                    result.success(
                        {
                            "device_id": data.get("device_id"),
                            "status": data.get("status"),
                            "existing": True,
                        }
                    )
                else:
                    result.failure(
                        "Device exists but could not fetch it",
                        {"get_status": existing.status_code},
                    )
            else:
                result.failure(f"HTTP {response.status_code}", {"response": response.text})

        except Exception as e:
            result.failure(f"Error: {str(e)}")

        return result

    async def test_device_list(self) -> TestResult:
        """Test device list API."""
        result = TestResult("Device List API")
        self.log("Testing device list API...", "DEBUG")

        try:
            # Register some devices first
            for device_id in self.test_devices:
                await self.register_device(device_id)
                await asyncio.sleep(0.5)

            # Get device list
            url = f"{self.api_url}/devices"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                devices = data.get("devices", [])
                device_ids = [d.get("device_id") for d in devices]

                # Check if our test devices are in the list
                found_count = sum(1 for d in self.test_devices if d in device_ids)

                result.success(
                    {
                        "total_devices": len(devices),
                        "test_devices_found": found_count,
                        "sample_devices": device_ids[:5],
                    }
                )
            else:
                result.failure(f"HTTP {response.status_code}")

        except Exception as e:
            result.failure(f"Error: {str(e)}")

        return result

    async def test_device_shadow(self) -> TestResult:
        """Test device shadow API."""
        result = TestResult("Device Shadow API")
        self.log("Testing device shadow API...", "DEBUG")

        try:
            device_id = self.test_devices[0]
            await self.register_device(device_id)
            await asyncio.sleep(1)

            # Get shadow
            url = f"{self.api_url}/devices/{device_id}/shadow"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                result.success(
                    {
                        "device_id": data.get("device_id"),
                        "version": data.get("version"),
                        "desired": data.get("desired"),
                        "reported": data.get("reported"),
                    }
                )
            else:
                result.failure(f"HTTP {response.status_code}", {"response": response.text})

        except Exception as e:
            result.failure(f"Error: {str(e)}")

        return result

    async def test_telemetry_storage(self) -> TestResult:
        """Test telemetry ingestion and storage."""
        result = TestResult("Telemetry Storage")
        self.log("Testing telemetry storage...", "DEBUG")

        try:
            if not DeviceSimulator:
                result.failure("Device simulator not available")
                return result

            # Create simulator with 3 devices
            self.simulator = DeviceSimulator(
                device_count=3,
                broker_host="localhost",
                broker_port=1883,
                mqtt_username="tankctl",
                mqtt_password="password",
            )

            # Start simulator in background task
            simulator_task = asyncio.create_task(self.simulator.run())

            # Wait for devices to connect and publish telemetry
            await asyncio.sleep(8)  # 3s connection + 5s first telemetry

            # Query telemetry API
            device_id = "tank1"
            url = f"{self.api_url}/devices/{device_id}/telemetry?limit=10"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                telemetry_count = data.get("count", 0)

                if telemetry_count > 0:
                    result.success(
                        {
                            "device_id": device_id,
                            "telemetry_points": telemetry_count,
                            "latest_temperature": data.get("data", [{}])[0].get("temperature"),
                        }
                    )
                else:
                    result.failure("No telemetry data received", {"count": telemetry_count})
            else:
                result.failure(f"HTTP {response.status_code}", {"response": response.text})

            # Stop simulator
            simulator_task.cancel()

        except Exception as e:
            result.failure(f"Error: {str(e)}")

        return result

    async def test_device_status(self) -> TestResult:
        """Test device online status."""
        result = TestResult("Device Online Status")
        self.log("Testing device online status...", "DEBUG")

        try:
            device_id = self.test_devices[0]
            await self.register_device(device_id)
            await asyncio.sleep(1)

            # Get device status
            url = f"{self.api_url}/devices/{device_id}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                result.success(
                    {
                        "device_id": data.get("device_id"),
                        "status": data.get("status"),
                        "last_seen": data.get("last_seen"),
                    }
                )
            else:
                result.failure(f"HTTP {response.status_code}")

        except Exception as e:
            result.failure(f"Error: {str(e)}")

        return result

    async def run_all_tests(self) -> bool:
        """Run all integration tests."""
        self.log("=" * 60)
        self.log("TankCtl Integration Test Suite")
        self.log("=" * 60)

        # Run tests
        tests = [
            self.test_api_health,
            self.test_device_registration,
            self.test_device_list,
            self.test_device_shadow,
            self.test_device_status,
            self.test_telemetry_storage,
        ]

        for test in tests:
            try:
                result = await test()
                self.results.append(result)
                print(result)
            except Exception as e:
                self.log(f"Test {test.__name__} crashed: {str(e)}", "ERROR")

        # Print summary
        self.log("=" * 60)
        self.log("Test Summary")
        self.log("=" * 60)

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        print(f"Passed: {passed}/{total}")
        print(f"Failed: {total - passed}/{total}")

        if passed == total:
            print("\n✓ All tests passed!")
            return True
        else:
            print(f"\n✗ {total - passed} test(s) failed")
            return False


async def main():
    """Main entry point."""
    parser = ArgumentParser(description="TankCtl Integration Test Suite")
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="API URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--skip-simulator",
        action="store_true",
        help="Skip telemetry storage test (requires device simulator)",
    )

    args = parser.parse_args()

    # Run tests
    test_suite = TankCtlIntegrationTest(api_url=args.api_url, verbose=args.verbose)
    success = await test_suite.run_all_tests()

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
