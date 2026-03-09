## Api Testing Guide

### Quick Start

**1. Start Docker services:**
```bash
docker-compose up -d
```

**2. Copy environment file:**
```bash
cp .env.example .env
```

**3. Run backend:**
```bash
# Using main.py with uvicorn
python src/main.py

# Or directly with uvicorn
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**4. Access Swagger UI:**
Open http://localhost:8000/docs

### Manual API Testing with curl

**Register a device:**
```bash
curl -X POST http://localhost:8000/devices \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "tank1",
    "device_secret": "my_secret"
  }'
```

**List devices:**
```bash
curl http://localhost:8000/devices
```

**Get device:**
```bash
curl http://localhost:8000/devices/tank1
```

**Get device shadow:**
```bash
curl http://localhost:8000/devices/tank1/shadow
```

**Update device shadow:**
```bash
curl -X PUT http://localhost:8000/devices/tank1/shadow \
  -H "Content-Type: application/json" \
  -d '{
    "desired": {"pump": "on", "light": "off"}
  }'
```

**Send light command:**
```bash
curl -X POST http://localhost:8000/devices/tank1/light \
  -H "Content-Type: application/json" \
  -d '{"state": "on"}'
```

**Send pump command:**
```bash
curl -X POST http://localhost:8000/devices/tank1/pump \
  -H "Content-Type: application/json" \
  -d '{"state": "off"}'
```

**Get command history:**
```bash
curl http://localhost:8000/devices/tank1/commands?limit=10
```

**Get telemetry:**
```bash
curl http://localhost:8000/devices/tank1/telemetry?limit=100
```

**Get specific metric:**
```bash
curl http://localhost:8000/devices/tank1/telemetry/temperature?limit=50
```

**Health check:**
```bash
curl http://localhost:8000/health
```

### Integration Test Flow

**1. Register device:**
```bash
curl -X POST http://localhost:8000/devices \
  -H "Content-Type: application/json" \
  -d '{"device_id": "test-device", "device_secret": "test"}'
```

**2. Simulate device heartbeat (via MQTT):**
```bash
# In another terminal
mosquitto_pub -h localhost -u tankctl -P password \
  -t "tankctl/test-device/heartbeat" \
  -m '{"uptime": 100}'
```

**3. Check device is now online:**
```bash
curl http://localhost:8000/devices/test-device
# Should return status: "online"
```

**4. Update desired state:**
```bash
curl -X PUT http://localhost:8000/devices/test-device/shadow \
  -H "Content-Type: application/json" \
  -d '{"desired": {"pump": "on"}}'
```

**5. Scheduler automatically reconciles (10s):**
- Logs show "shadow_reconciled" for device
- Command published to MQTT topic

**6. Simulate device reporting state:**
```bash
mosquitto_pub -h localhost -u tankctl -P password \
  -t "tankctl/test-device/reported" \
  -m '{"pump": "on"}'
```

**7. Verify shadow is now synchronized:**
```bash
curl http://localhost:8000/devices/test-device/shadow
# Should return synchronized: true
```

### Monitoring

**View API logs:**
```bash
# Stream logs from backend
docker-compose logs -f backend
```

**View MQTT messages:**
```bash
# Subscribe to all tank topics
mosquitto_sub -h localhost -u tankctl -P password \
  -t 'tankctl/#' -v
```

**Check database:**
```bash
# Connect to PostgreSQL
psql postgresql://tankctl:password@localhost:5432/tankctl

# List devices
SELECT device_id, status, last_seen FROM devices;

# View shadows
SELECT device_id, version, desired, reported FROM device_shadows;

# View commands
SELECT device_id, command, status, version FROM commands ORDER BY created_at DESC LIMIT 10;
```

### Common Issues

**Connection refused on MQTT:**
```bash
# Verify Mosquitto is running
docker-compose ps | grep mosquitto

# Check MQTT logs
docker-compose logs mosquitto
```

**Database connection error:**
```bash
# Verify PostgreSQL is running
docker-compose ps | grep postgres

# Check PostgreSQL logs
docker-compose logs postgres
```

**API port already in use:**
```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
python -m uvicorn src.api.main:app --port 8001
```

**Import errors:**
```bash
# Ensure you're in the tankctl root directory
cd /home/lokesh/tankctl

# Verify PYTHONPATH includes src
export PYTHONPATH=/home/lokesh/tankctl:$PYTHONPATH

# Run again
python src/main.py
```

### Performance Testing

**Load test with concurrent requests:**
```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/devices

# Using hey
go install github.com/rakyll/hey@latest
hey -n 1000 -c 10 http://localhost:8000/devices
```

**Monitor scheduler tasks:**
```bash
# Add debug logging
DEBUG=true python src/main.py

# Watch for reconciliation logs
grep "shadow_reconciled" backend.log
```

### API Response Examples

**Successful device registration:**
```json
{
  "device_id": "tank1",
  "status": "offline",
  "firmware_version": null,
  "created_at": 1705316400,
  "last_seen": null
}
```

**Device list:**
```json
{
  "count": 2,
  "devices": [
    {
      "device_id": "tank1",
      "status": "online",
      "firmware_version": "1.2.3",
      "created_at": 1705316400,
      "last_seen": 1705316500
    },
    {
      "device_id": "tank2",
      "status": "offline",
      "firmware_version": null,
      "created_at": 1705316410,
      "last_seen": null
    }
  ]
}
```

**Shadow response:**
```json
{
  "device_id": "tank1",
  "desired": {
    "pump": "on",
    "light": "off"
  },
  "reported": {
    "pump": "off",
    "light": "off"
  },
  "version": 5,
  "synchronized": false
}
```

**Command acceptance:**
```json
{
  "command_id": "tank1",
  "device_id": "tank1",
  "command": "set_pump",
  "value": "on",
  "version": 6,
  "status": "pending"
}
```
