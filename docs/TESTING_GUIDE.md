"""
TankCtl Backend - Testing Guide

Quick reference for testing the implemented components.
"""

# ============================================================================
# QUICK START: Run Backend
# ============================================================================
"""
1. Start infrastructure:
   docker-compose up -d

2. Wait for services to be ready:
   docker-compose ps
   (All should be in "healthy" state)

3. Install dependencies:
   pip install -r requirements.txt

4. Configure environment:
   cp .env.example .env
   # Edit .env if needed (defaults work with docker-compose)

5. Terminal 1 - Run backend (MQTT + Scheduler):
   python -m src.main
   
   Expected output:
   ---
   tankctl_initializing
   database_initialization_complete
   mqtt_handlers_registered
   mqtt_connected
   scheduler_started
   tankctl_backend_started
   ---

6. Terminal 2 - Run API server:
   uvicorn src.server:app --reload --port 8000
   
   Open: http://localhost:8000/docs (Swagger UI)
"""

# ============================================================================
# TEST SCENARIO: Device Shadow and Reconciliation
# ============================================================================
"""
This scenario tests the complete device shadow workflow.

Timeline:
  1. Register device
  2. Device sends heartbeat (marked online)
  3. API sets desired state
  4. Device reports different state (drift detected)
  5. Scheduler reconciliation runs
  6. Device receives command and updates reported state
  7. States sync automatically
"""

# ============================================================================
# STEP 1: Register Device
# ============================================================================
"""
curl -X POST http://localhost:8000/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "tank1",
    "device_secret": "8fa93d72c6c5a91d"
  }'

Response:
{
  "device_id": "tank1",
  "status": "offline",
  "firmware_version": null,
  "created_at": "2026-03-04T10:30:00.000000",
  "last_seen": "2026-03-04T10:30:00.000000"
}

Backend logs:
{
  "timestamp": "2026-03-04T10:30:00.123456",
  "event": "device_registered",
  "device_id": "tank1"
}
"""

# ============================================================================
# STEP 2: Get Device Shadow
# ============================================================================
"""
curl http://localhost:8000/api/devices/tank1/shadow

Expected response:
{
  "device_id": "tank1",
  "desired": {},
  "reported": {},
  "version": 0,
  "synchronized": true
}

Explanation:
- Device was just created
- No desired state yet
- No reported state yet
- Version 0 (first version)
- Synchronized: true (both empty)
"""

# ============================================================================
# STEP 3: Device Sends Heartbeat
# ============================================================================
"""
In another terminal, use mosquitto_pub to simulate device:

mosquitto_pub -h localhost -u tankctl -P password \
  -t "tankctl/tank1/heartbeat" \
  -m '{"status": "online", "uptime": 120}'

Alternative (using docker):
docker exec tankctl-mosquitto mosquitto_pub \
  -u tankctl -P password \
  -t "tankctl/tank1/heartbeat" \
  -m '{"status": "online", "uptime": 120}'

Backend logs:
{
  "timestamp": "2026-03-04T10:30:05.123456",
  "event": "device_heartbeat_handled",
  "device_id": "tank1"
}

Device now online:
curl http://localhost:8000/api/devices/tank1

Response.status = "online"
Response.last_seen = current_time
"""

# ============================================================================
# STEP 4: Set Desired State (API)
# ============================================================================
"""
curl -X PUT http://localhost:8000/api/devices/tank1/shadow \
  -H "Content-Type: application/json" \
  -d '{
    "desired": {
      "light": "on",
      "pump": "off"
    }
  }'

Response:
{
  "device_id": "tank1",
  "desired": {
    "light": "on",
    "pump": "off"
  },
  "reported": {},
  "version": 1,
  "synchronized": false
}

Backend logs:
{
  "timestamp": "2026-03-04T10:30:10.123456",
  "event": "setting_desired_state",
  "device_id": "tank1"
}
{
  "timestamp": "2026-03-04T10:30:10.234567",
  "event": "desired_state_updated",
  "device_id": "tank1",
  "version": 1
}

Note: synchronized = false because desired != reported
"""

# ============================================================================
# STEP 5: Device Sends Reported State
# ============================================================================
"""
Device reports current state (different from desired):

mosquitto_pub -h localhost -u tankctl -P password \
  -t "tankctl/tank1/reported" \
  -m '{"light": "off", "pump": "on"}'

Backend logs:
{
  "timestamp": "2026-03-04T10:30:15.123456",
  "event": "reported_state_handled",
  "device_id": "tank1"
}

Check shadow again:
curl http://localhost:8000/api/devices/tank1/shadow

Response:
{
  "device_id": "tank1",
  "desired": {
    "light": "on",
    "pump": "off"
  },
  "reported": {
    "light": "off",
    "pump": "on"
  },
  "version": 1,
  "synchronized": false
}

Note:
- desired != reported
- synchronized = false
- Reconciliation will detect this drift
"""

# ============================================================================
# STEP 6: Wait for Scheduler Reconciliation
# ============================================================================
"""
The "shadow reconciliation" job runs every 60 seconds (default).

To see it in action, you can:
1. Wait 60 seconds for automatic run, OR
2. Reduce SHADOW_RECONCILIATION_INTERVAL in .env to 10 seconds
3. Or manually trigger by modifying scheduler test code

Backend logs when reconciliation detects drift:
{
  "timestamp": "2026-03-04T10:31:15.123456",
  "event": "shadow_reconciliation_started",
  "device_id": "tank1"
}
{
  "timestamp": "2026-03-04T10:31:15.234567",
  "event": "shadow_reconciliation_needed",
  "device_id": "tank1",
  "delta": {
    "light": "on",
    "pump": "off"
  }
}
{
  "timestamp": "2026-03-04T10:31:15.345678",
  "event": "command_sent",
  "device_id": "tank1",
  "command": "set_multiple_states"
}

Commands would be published to: tankctl/tank1/command

Note: Current implementation logs delta but full command publishing
      can be extended based on device_specific commands.
"""

# ============================================================================
# STEP 7: Device Executes Commands
# ============================================================================
"""
Device receives command from tankctl/tank1/command and executes.

Then device reports updated state:

mosquitto_pub -h localhost -u tankctl -P password \
  -t "tankctl/tank1/reported" \
  -m '{"light": "on", "pump": "off"}'

Backend logs:
{
  "timestamp": "2026-03-04T10:31:20.123456",
  "event": "shadow_reported_state_updated",
  "device_id": "tank1",
  "synchronized": true
}

Check shadow:
curl http://localhost:8000/api/devices/tank1/shadow

Response:
{
  "device_id": "tank1",
  "desired": {
    "light": "on",
    "pump": "off"
  },
  "reported": {
    "light": "on",
    "pump": "off"
  },
  "version": 1,
  "synchronized": true
}

SUCCESS: States are now synchronized!
"""

# ============================================================================
# SCENARIO 2: Device Health Monitoring
# ============================================================================
"""
Test device offline detection:

1. Device sends heartbeat (online)
   mosquitto_pub -u tankctl -P password -t "tankctl/tank2/heartbeat" -m '{}'
   
2. Check device:
   curl http://localhost:8000/api/devices/tank2
   Response.status = "online"

3. Wait > 60 seconds without heartbeat

4. Observe health check job runs
   Backend logs show device went offline
   
5. Check device:
   curl http://localhost:8000/api/devices/tank2
   Response.status = "offline"
"""

# ============================================================================
# SCENARIO 3: Telemetry Storage
# ============================================================================
"""
Device sends telemetry every 30 seconds:

for i in {1..5}; do
  mosquitto_pub -u tankctl -P password \
    -t "tankctl/tank1/telemetry" \
    -m "{\"temperature\": $((20 + i)), \"humidity\": 60}"
  sleep 10
done

Backend logs:
{
  "timestamp": "...",
  "event": "telemetry_handled",
  "device_id": "tank1"
}
{
  "timestamp": "...",
  "event": "telemetry_stored",
  "device_id": "tank1"
}

Data stored in TimescaleDB automatically.
Query external tools can read from TimescaleDB for visualization.
"""

# ============================================================================
# SCENARIO 4: Multiple Devices
# ============================================================================
"""
Register multiple devices:

curl -X POST http://localhost:8000/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{"device_id": "tank2", "device_secret": "secret2"}'

curl -X POST http://localhost:8000/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{"device_id": "pump1", "device_secret": "secret3"}'

List all:
curl http://localhost:8000/api/devices

Scheduler automatically watches ALL devices:
- Checks heartbeats for each
- Reconciles shadows for each
- Handles messages from each
"""

# ============================================================================
# MONITORING & DEBUGGING
# ============================================================================
"""
1. Check MQTT connection status:
   curl http://localhost:8000/health
   
   Response indicates if backend → MQTT is connected

2. View backend logs:
   docker logs tankctl-mosquitto
   
3. View database:
   psql postgresql://tankctl:password@localhost:5432/tankctl -c "SELECT * FROM devices;"
   psql postgresql://tankctl:password@localhost:5432/tankctl -c "SELECT * FROM device_shadows;"

4. Monitor MQTT:
   mosquitto_sub -h localhost -u tankctl -P password -v -t 'tankctl/#'
   (Shows all MQTT traffic)

5. Test endpoints:
   http://localhost:8000/docs (Swagger UI)
"""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================
"""
Problem: Device marked offline immediately
Solution: Increase DEVICE_OFFLINE_TIMEOUT in .env (default 60)

Problem: Commands not reaching device
Solution: Check mosquitto:
  - Verify credentials match
  - Check QoS levels
  - Verify topic subscriptions

Problem: Telemetry not stored
Solution: Check TimescaleDB:
  - Verify connection in .env
  - Check TIME column in hypertable

Problem: Scheduler jobs not running
Solution: Check logs:
  - Scheduler should log job execution
  - Check APScheduler configuration

Problem: Database errors
Solution:
  - Verify PostgreSQL is running
  - Check connection string in .env
  - Tables should auto-create on first run
"""

# ============================================================================
# KEY ATTRIBUTES TO VERIFY
# ============================================================================
"""
Device Shadow Response Fields:
  - device_id: Current device
  - desired: Backend's target state
  - reported: Device's actual state
  - version: Incrementing counter
  - synchronized: desired == reported

MQTT Message Format (Command):
  {
    "version": 5,
    "command": "set_light",
    "value": "on"
  }

Device Timestamps:
  - created_at: When device was registered
  - last_seen: Last heartbeat/activity
  - If now() - last_seen > timeout → mark offline

Shadow Timestamps:
  - created_at: When shadow was created
  - updated_at: Last time any field changed
  - used to track synchronization
"""

# ============================================================================
# EXPECTED LOG PATTERN
# ============================================================================
"""
Normal operation shows this pattern:

t=0s:    device_registered, shadow_created
t=5s:    device_heartbeat_handled, device status online
t=10s:   desired_state_updated, version incremented
t=15s:   shadow_reported_state_updated
t=30s:   heartbeat_check_job_starting (device health check)
t=60s:   shadow_reconciliation_job_starting
t=60s:   shadow_reconciliation_needed (if drift exists)
t=60s:   command_sent (if reconciliation triggered)

If all states match, you'll see:
         shadow_already_synchronized

Repeats every 60 seconds (reconciliation interval).
"""
