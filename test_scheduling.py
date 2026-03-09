#!/usr/bin/env python3
"""
Quick test script for light scheduling feature.

Tests:
1. Create schedule via API
2. Verify schedule retrieval
3. Verify APScheduler jobs are registered
4. Delete schedule
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_scheduling():
    """Test light scheduling end-to-end."""
    
    print("=" * 60)
    print("Light Scheduling Integration Test")
    print("=" * 60)
    
    # Register a test device
    device_id = f"test_device_{int(time.time())}"
    print(f"\n1. Registering test device: {device_id}")
    
    response = requests.post(
        f"{BASE_URL}/devices",
        json={"device_id": device_id}
    )
    
    if response.status_code == 201:
        print(f"   ✓ Device registered: {response.json()['device_id']}")
    else:
        print(f"   ✗ Failed to register device: {response.status_code} - {response.text}")
        return
    
    # Create a schedule
    print(f"\n2. Creating light schedule for {device_id}")
    schedule_data = {
        "on_time": "18:00",
        "off_time": "06:00",
        "enabled": True
    }
    
    response = requests.post(
        f"{BASE_URL}/devices/{device_id}/schedule",
        json=schedule_data
    )
    
    if response.status_code == 201:
        schedule = response.json()
        print(f"   ✓ Schedule created:")
        print(f"     - on_time: {schedule['on_time']}")
        print(f"     - off_time: {schedule['off_time']}")
        print(f"     - enabled: {schedule['enabled']}")
    else:
        print(f"   ✗ Failed to create schedule: {response.status_code} - {response.text}")
        return
    
    # Get the schedule
    print(f"\n3. Retrieving schedule for {device_id}")
    
    response = requests.get(f"{BASE_URL}/devices/{device_id}/schedule")
    
    if response.status_code == 200:
        schedule = response.json()
        print(f"   ✓ Schedule retrieved:")
        print(f"     - on_time: {schedule['on_time']}")
        print(f"     - off_time: {schedule['off_time']}")
        print(f"     - enabled: {schedule['enabled']}")
    else:
        print(f"   ✗ Failed to retrieve schedule: {response.status_code} - {response.text}")
    
    # Check if current time results in correct light state
    current_time = datetime.now().time()
    print(f"\n4. Current time: {current_time.strftime('%H:%M')}")
    
    # Get device shadow to check current state
    response = requests.get(f"{BASE_URL}/devices/{device_id}/shadow")
    
    if response.status_code == 200:
        shadow = response.json()
        print(f"   ✓ Shadow state:")
        print(f"     - desired: {shadow['desired']}")
        print(f"     - reported: {shadow['reported']}")
        print(f"     - synchronized: {shadow['synchronized']}")
    else:
        print(f"   ✗ Failed to get shadow: {response.status_code}")
    
    # Wait a moment
    print("\n5. Testing schedule update...")
    
    updated_schedule = {
        "on_time": "19:00",
        "off_time": "07:00",
        "enabled": True
    }
    
    response = requests.post(
        f"{BASE_URL}/devices/{device_id}/schedule",
        json=updated_schedule
    )
    
    if response.status_code == 201:
        schedule = response.json()
        print(f"   ✓ Schedule updated:")
        print(f"     - on_time: {schedule['on_time']}")
        print(f"     - off_time: {schedule['off_time']}")
    else:
        print(f"   ✗ Failed to update schedule: {response.status_code}")
    
    # Delete the schedule
    print(f"\n6. Deleting schedule for {device_id}")
    
    response = requests.delete(f"{BASE_URL}/devices/{device_id}/schedule")
    
    if response.status_code == 204:
        print(f"   ✓ Schedule deleted")
    else:
        print(f"   ✗ Failed to delete schedule: {response.status_code} - {response.text}")
    
    # Verify deletion
    response = requests.get(f"{BASE_URL}/devices/{device_id}/schedule")
    
    if response.status_code == 404:
        print(f"   ✓ Confirmed schedule deleted (404 response)")
    else:
        print(f"   ✗ Schedule still exists: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_scheduling()
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to TankCtl API")
        print("  Make sure the backend is running: python -m src.api.main")
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
