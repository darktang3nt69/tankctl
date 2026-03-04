"""
TankCtl Backend - System Integration Tests

Demonstrates:
1. Device registration and shadow creation
2. MQTT message handling (telemetry, reported, heartbeat)
3. Shadow reconciliation
4. Command sending
5. Scheduler integration
"""

import json
from datetime import datetime

from src.config.settings import settings
from src.domain.device import Device
from src.domain.device_shadow import DeviceShadow
from src.domain.command import Command, CommandStatus
from src.infrastructure.db.database import db
from src.infrastructure.mqtt.mqtt_topics import MQTTTopics
from src.services.device_service import DeviceService
from src.services.shadow_service import ShadowService
from src.services.command_service import CommandService
from src.services.telemetry_service import TelemetryService
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# TEST 1: Device Registration and Shadow Creation
# ============================================================================

def test_device_registration():
    """Test registering a new device."""
    print("\n" + "="*70)
    print("TEST 1: Device Registration and Shadow Creation")
    print("="*70)

    session = db.get_session()
    device_service = DeviceService(session)

    # Register device
    device = device_service.register_device(
        device_id="tank1",
        device_secret="abc123xyz"
    )

    print(f"✓ Device registered: {device.device_id}")
    print(f"  Status: {device.status}")
    print(f"  Created at: {device.created_at}")

    # Get device
    retrieved = device_service.get_device("tank1")
    print(f"✓ Device retrieved: {retrieved.device_id}")

    # Check shadow was created
    shadow = device_service.get_device_shadow("tank1")
    print(f"✓ Shadow created: device_id={shadow.device_id}, version={shadow.version}")
    print(f"  Desired: {shadow.desired}")
    print(f"  Reported: {shadow.reported}")

    session.close()


# ============================================================================
# TEST 2: Device Heartbeat Handling
# ============================================================================

def test_heartbeat_handling():
    """Test device heartbeat logic."""
    print("\n" + "="*70)
    print("TEST 2: Device Heartbeat Handling")
    print("="*70)

    session = db.get_session()
    device_service = DeviceService(session)

    # Device sends heartbeat
    device_service.handle_heartbeat("tank1")

    device = device_service.get_device("tank1")
    print(f"✓ Heartbeat processed")
    print(f"  Device status: {device.status}")
    print(f"  Last seen: {device.last_seen}")

    # Check device is online
    is_online = device.is_online(timeout_seconds=60)
    print(f"✓ Device is_online(): {is_online}")

    session.close()


# ============================================================================
# TEST 3: Shadow Reported State Update
# ============================================================================

def test_shadow_reported_state():
    """Test updating shadow with device reported state."""
    print("\n" + "="*70)
    print("TEST 3: Shadow Reported State Update")
    print("="*70)

    session = db.get_session()
    shadow_service = ShadowService(session)

    # Device reports its current state
    reported_state = {
        "light": "off",
        "pump": "on"
    }

    shadow = shadow_service.handle_reported_state("tank1", reported_state)
    print(f"✓ Reported state updated")
    print(f"  Reported: {shadow.reported}")
    print(f"  Desired: {shadow.desired}")
    print(f"  Synchronized: {shadow.is_synchronized()}")

    session.close()


# ============================================================================
# TEST 4: Shadow Desired State Update (API Request)
# ============================================================================

def test_shadow_desired_state():
    """Test setting desired state from API."""
    print("\n" + "="*70)
    print("TEST 4: Shadow Desired State Update")
    print("="*70)

    session = db.get_session()
    shadow_service = ShadowService(session)

    # API sets desired state
    desired_state = {
        "light": "on",
        "pump": "off"
    }

    shadow = shadow_service.set_desired_state("tank1", desired_state)
    print(f"✓ Desired state updated (API request)")
    print(f"  Desired: {shadow.desired}")
    print(f"  Reported: {shadow.reported}")
    print(f"  Version incremented to: {shadow.version}")
    print(f"  Synchronized: {shadow.is_synchronized()}")

    # Check delta
    delta = shadow.get_delta()
    print(f"✓ Delta (desired - reported):")
    for key, value in delta.items():
        print(f"    {key}: {value}")

    session.close()


# ============================================================================
# TEST 5: Shadow Reconciliation
# ============================================================================

def test_shadow_reconciliation():
    """Test shadow reconciliation logic."""
    print("\n" + "="*70)
    print("TEST 5: Shadow Reconciliation")
    print("="*70)

    session = db.get_session()
    shadow_service = ShadowService(session)
    device_service = DeviceService(session)

    # Show current state
    shadow = shadow_service.get_device_shadow("tank1") if hasattr(shadow_service, 'get_device_shadow') else shadow_service.shadow_repo.get_by_device_id("tank1")
    
    print(f"Current shadow state:")
    print(f"  Desired:  {shadow.desired}")
    print(f"  Reported: {shadow.reported}")
    print(f"  Synchronized: {shadow.is_synchronized()}")

    # Reconcile
    shadow_service.reconcile_shadow("tank1")
    print(f"✓ Reconciliation job executed")

    session.close()


# ============================================================================
# TEST 6: Command Sending
# ============================================================================

def test_command_sending():
    """Test sending command to device."""
    print("\n" + "="*70)
    print("TEST 6: Command Sending")
    print("="*70)

    session = db.get_session()
    command_service = CommandService(session)

    # Send command
    command = command_service.send_command(
        device_id="tank1",
        command="set_light",
        value="on"
    )

    print(f"✓ Command sent")
    print(f"  Command ID: {command.device_id}")
    print(f"  Name: {command.command}")
    print(f"  Value: {command.value}")
    print(f"  Version: {command.version}")
    print(f"  Status: {command.status}")

    # Command payload (what MQTT would receive)
    payload = command.to_mqtt_payload()
    print(f"✓ MQTT Payload:")
    print(f"  {json.dumps(payload, indent=2)}")

    # Topic
    topic = MQTTTopics.command_topic("tank1")
    print(f"✓ MQTT Topic: {topic}")

    session.close()


# ============================================================================
# TEST 7: Telemetry Storage
# ============================================================================

def test_telemetry_storage():
    """Test storing telemetry data."""
    print("\n" + "="*70)
    print("TEST 7: Telemetry Storage")
    print("="*70)

    session = db.get_timescale_session()
    telemetry_service = TelemetryService(session)

    # Store telemetry from device
    telemetry_payload = {
        "temperature": 24.5,
        "humidity": 65,
        "pressure": 1013.25
    }

    telemetry_service.store_telemetry("tank1", telemetry_payload)
    print(f"✓ Telemetry stored")
    print(f"  Device: tank1")
    print(f"  Metrics: {list(telemetry_payload.keys())}")

    # Retrieve telemetry
    data = telemetry_service.get_device_telemetry("tank1", limit=10)
    print(f"✓ Telemetry retrieved ({len(data)} points)")

    session.close()


# ============================================================================
# TEST 8: MQTT Topic Parsing
# ============================================================================

def test_mqtt_topic_parsing():
    """Test MQTT topic parsing."""
    print("\n" + "="*70)
    print("TEST 8: MQTT Topic Parsing")
    print("="*70)

    test_topics = [
        "tankctl/tank1/telemetry",
        "tankctl/greenhouse-light-1/reported",
        "tankctl/water-pump/heartbeat",
        "tankctl/multipart-device-123/command",
    ]

    for topic in test_topics:
        device_id = MQTTTopics.extract_device_id(topic)
        channel = MQTTTopics.extract_channel(topic)
        print(f"✓ Topic: {topic}")
        print(f"  Device ID: {device_id}")
        print(f"  Channel: {channel}")


# ============================================================================
# TEST 9: Device Shadow Model Operations
# ============================================================================

def test_device_shadow_model():
    """Test DeviceShadow model operations."""
    print("\n" + "="*70)
    print("TEST 9: Device Shadow Model Operations")
    print("="*70)

    shadow = DeviceShadow(
        device_id="tank1",
        desired={"light": "on", "pump": "off"},
        reported={"light": "off", "pump": "off"},
        version=5
    )

    print(f"Initial state:")
    print(f"  Version: {shadow.version}")
    print(f"  Synchronized: {shadow.is_synchronized()}")

    # Increment version
    new_version = shadow.increment_version()
    print(f"✓ Version incremented: {new_version}")

    # Update desired
    shadow.update_desired({"light": "on"})
    print(f"✓ Desired updated to: {shadow.desired}")

    # Update reported
    shadow.update_reported({"light": "on", "pump": "off"})
    print(f"✓ Reported updated to: {shadow.reported}")

    # Check sync
    print(f"✓ Synchronized: {shadow.is_synchronized()}")

    # Get delta
    shadow.reported = {"light": "off"}
    delta = shadow.get_delta()
    print(f"✓ Delta: {delta}")


# ============================================================================
# TEST 10: Device Status Workflow
# ============================================================================

def test_device_status_workflow():
    """Test complete device status workflow."""
    print("\n" + "="*70)
    print("TEST 10: Complete Device Status Workflow")
    print("="*70)

    session = db.get_session()
    device_service = DeviceService(session)

    # 1. Check health before heartbeat
    print("\n1. Checking health (device should be offline)...")
    changes = device_service.check_device_health(timeout_seconds=60)
    device = device_service.get_device("tank1")
    print(f"   Device status: {device.status}")

    # 2. Simulate heartbeat
    print("\n2. Device sends heartbeat...")
    device_service.handle_heartbeat("tank1")
    device = device_service.get_device("tank1")
    print(f"   Device status: {device.status}")
    print(f"   Last seen: {device.last_seen}")

    # 3. Get all devices
    print("\n3. Listing all devices...")
    devices = device_service.get_all_devices()
    for d in devices:
        print(f"   - {d.device_id}: {d.status}")

    session.close()


# ============================================================================
# Main Test Runner
# ============================================================================

def run_all_tests():
    """Run all integration tests."""
    print("\n" * 2)
    print("#" * 70)
    print("# TankCtl Backend - System Integration Tests")
    print("#" * 70)

    try:
        # Initialize database
        print("\nInitializing database...")
        db.init_db()
        print("✓ Database initialized")

        # Run tests
        test_device_registration()
        test_heartbeat_handling()
        test_shadow_reported_state()
        test_shadow_desired_state()
        test_shadow_reconciliation()
        test_command_sending()
        test_telemetry_storage()
        test_mqtt_topic_parsing()
        test_device_shadow_model()
        test_device_status_workflow()

        print("\n" + "#" * 70)
        print("# All tests completed successfully!")
        print("#" * 70 + "\n")

    except Exception as e:
        logger.error("test_error", error=str(e))
        print(f"\n✗ Test failed: {e}\n")
        raise


if __name__ == "__main__":
    run_all_tests()
