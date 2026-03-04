## Telemetry Testing Guide

### Quick Start

**1. Start all services:**
```bash
docker-compose up -d
```

**2. Run migrations:**
```bash
# Connect to TimescaleDB and run migration
psql postgresql://tankctl:password@localhost:5432/tankctl_telemetry < migrations/001_create_telemetry_table.sql

# Or manually:
psql postgresql://tankctl:password@localhost:5432/tankctl_telemetry
\i migrations/001_create_telemetry_table.sql
```

**3. Start backend:**
```bash
python src/main.py
```

**4. Test API:**
```bash
# Register device
curl -X POST http://localhost:8000/devices \
  -H "Content-Type: application/json" \
  -d '{"device_id": "tank1", "device_secret": "secret"}'

# Open telemetry endpoint
curl http://localhost:8000/devices/tank1/telemetry
```

### Unit Tests

Test repository layer:
```python
import pytest
from sqlalchemy.orm import Session
from datetime import datetime
from src.repository.telemetry_repository import TelemetryRepository

def test_insert_telemetry():
    """Test inserting telemetry record."""
    # Use test database session
    repo = TelemetryRepository(test_session)
    
    repo.insert(
        device_id="tank1",
        temperature=24.5,
        humidity=65.2,
        pressure=1013.25
    )
    
    # Verify record exists
    results = repo.get_recent("tank1", limit=1)
    assert len(results) == 1
    assert results[0]["temperature"] == 24.5

def test_get_by_metric():
    """Test retrieving specific metric."""
    repo = TelemetryRepository(test_session)
    
    # Insert multiple records
    for i in range(10):
        repo.insert("tank1", temperature=20+i)
    
    # Get temperature metric
    results = repo.get_by_metric("tank1", metric="temperature", limit=100)
    assert len(results) == 10
    assert "value" in results[0]
```

### Integration Tests

**Test MQTT to API flow:**
```bash
# Terminal 1: Start backend
python src/main.py

# Terminal 2: Publish telemetry
mosquitto_pub -h localhost -u tankctl -P password \
  -t "tankctl/tank1/telemetry" \
  -m '{"temperature": 24.5, "humidity": 65.2}'

sleep 2

# Terminal 3: Query API
curl http://localhost:8000/devices/tank1/telemetry

# Expected response:
# {
#   "device_id": "tank1",
#   "count": 1,
#   "data": [
#     {
#       "time": "2025-01-15T10:30:00+00:00",
#       "temperature": 24.5,
#       "humidity": 65.2,
#       "pressure": null,
#       "metadata": null
#     }
#   ]
# }
```

### API Endpoint Tests

**Test 1: Store and retrieve telemetry**
```bash
# Publish telemetry
for i in {1..10}; do
  mosquitto_pub -h localhost -u tankctl -P password \
    -t "tankctl/tank1/telemetry" \
    -m "{\"temperature\": $((20 + RANDOM % 10)), \"humidity\": $((60 + RANDOM % 20))}"
  sleep 1
done

# Get recent telemetry
curl "http://localhost:8000/devices/tank1/telemetry?limit=5"

# Assert: count = 5, all records have time, temperature, humidity
```

**Test 2: Get specific metric**
```bash
# Get only temperature readings
curl "http://localhost:8000/devices/tank1/telemetry/temperature?limit=10"

# Expected:
# {
#   "device_id": "tank1",
#   "metric": "temperature",
#   "count": 10,
#   "data": [
#     {"time": "...", "device_id": "tank1", "value": 24.5}
#   ]
# }

# Try invalid metric
curl "http://localhost:8000/devices/tank1/telemetry/invalid"
# Expected: 400 Bad Request
```

**Test 3: Get hourly summary**
```bash
# Get hourly aggregates
curl "http://localhost:8000/devices/tank1/telemetry/hourly/summary?hours=24"

# Expected:
# {
#   "device_id": "tank1",
#   "count": <N>,
#   "data": [
#     {
#       "hour": "2025-01-14T10:00:00+00:00",
#       "temperature": {
#         "avg": 24.2,
#         "max": 25.1,
#         "min": 23.5
#       },
#       "humidity": {...},
#       "sample_count": 120
#     }
#   ]
# }
```

### Manual Database Tests

**Test database connectivity:**
```bash
psql postgresql://tankctl:password@localhost:5432/tankctl_telemetry

# Verify hypertable
SELECT hypertable_name FROM timescaledb_information.hypertables;
# Expected: telemetry

# Check indexes
SELECT indexname FROM pg_indexes WHERE tablename = 'telemetry';
# Expected: multiple indexes

# Check retention policy
SELECT * FROM timescaledb_information.policy;
# Expected: 30-day retention
```

**Test direct insertion:**
```sql
INSERT INTO telemetry (time, device_id, temperature, humidity, pressure)
VALUES (NOW(), 'tank1', 24.5, 65.2, 1013.25);

-- Verify
SELECT * FROM telemetry WHERE device_id = 'tank1' ORDER BY time DESC LIMIT 1;
```

**Test continuous aggregate:**
```sql
-- Verify view exists
SELECT * FROM information_schema.views WHERE table_name = 'telemetry_hourly';

-- Query hourly data
SELECT * FROM telemetry_hourly 
WHERE device_id = 'tank1' 
  AND hour > NOW() - INTERVAL '24 hours'
ORDER BY hour DESC;
```

### Performance Tests

**Load test: 10,000 inserts**
```bash
#!/bin/bash
# save as load_test.sh

for i in {1..10000}; do
  TEMP=$(echo "20 + ($i % 10)" | bc)
  HUMID=$(echo "60 + ($i % 20)" | bc)
  
  mosquitto_pub -h localhost -u tankctl -P password \
    -t "tankctl/tank1/telemetry" \
    -m "{\"temperature\": $TEMP, \"humidity\": $HUMID}" &
  
  # Batch 100 at a time
  if (( i % 100 == 0 )); then
    wait
    echo "Inserted $i records"
  fi
done
wait
echo "Load test complete: 10,000 records"
```

**Query performance:**
```bash
# Time query
time curl "http://localhost:8000/devices/tank1/telemetry?limit=1000"

# Expected: < 100ms for 1000 records
```

**Storage test:**
```sql
-- Check disk usage
SELECT pg_size_pretty(pg_total_relation_size('telemetry')) as telemetry_size;

-- Check chunk count
SELECT chunk_name FROM timescaledb_information.chunks WHERE hypertable_name = 'telemetry';

-- Check compression
SELECT chunk_name, is_compressed FROM timescaledb_information.chunks WHERE hypertable_name = 'telemetry';
```

### Error Handling Tests

**Test invalid device_id:**
```bash
curl "http://localhost:8000/devices/nonexistent/telemetry"
# Expected: 200 OK with empty data array
```

**Test invalid metric:**
```bash
curl "http://localhost:8000/devices/tank1/telemetry/invalid"
# Expected: 400 Bad Request
```

**Test invalid query parameters:**
```bash
# Limit too high
curl "http://localhost:8000/devices/tank1/telemetry?limit=20000"
# Expected: 400 Bad Request

# Negative hours
curl "http://localhost:8000/devices/tank1/telemetry?hours=-5"
# Expected: 400 Bad Request

# Invalid hours for summary
curl "http://localhost:8000/devices/tank1/telemetry/hourly/summary?hours=10000"
# Expected: 400 Bad Request
```

### MQTT Handler Tests

**Test TelemetryHandler integration:**
```python
def test_telemetry_handler():
    """Test MQTT telemetry handler."""
    from src.infrastructure.mqtt.handlers import TelemetryHandler
    from src.infrastructure.db.database import db
    
    handler = TelemetryHandler()
    session = db.get_timescale_session()
    
    payload = {
        "temperature": 24.5,
        "humidity": 65.2,
        "pressure": 1013.25,
        "metadata": {"location": "sensor_1"}
    }
    
    handler.handle("tank1", payload)
    
    # Verify data in database
    from src.repository.telemetry_repository import TelemetryRepository
    repo = TelemetryRepository(session)
    results = repo.get_recent("tank1", limit=1)
    
    assert len(results) == 1
    assert results[0]["temperature"] == 24.5
    
    session.close()
```

**Test invalid payload:**
```python
def test_invalid_payload():
    """Test handler with invalid payload."""
    handler = TelemetryHandler()
    
    # Empty payload
    handler.handle("tank1", {})
    # Expected: warning logged, no error
    
    # Non-numeric values
    handler.handle("tank1", {"temperature": "invalid"})
    # Expected: error logged, conversion fails
    
    # Partial payload
    handler.handle("tank1", {"temperature": 24.5})
    # Expected: only temperature stored, no error
```

### Grafana Dashboard Tests

**Test dashboard loads:**
1. Open Grafana: http://localhost:3000
2. Login (default: admin/admin)
3. Go to Dashboards → Manage
4. Search for "TankCtl Telemetry"
5. Verify dashboard loads without errors

**Test dashboard panels:**
1. **Temperature Chart** - Should show line graph of temperature over time
2. **Humidity Chart** - Should show line graph of humidity over time  
3. **Temperature Stats** - Should show current temperature value
4. **Humidity Stats** - Should show current humidity value
5. **Device Selector** - Should have dropdown with available devices

**Test interactive features:**
1. Change time range (top right) - charts should update
2. Select different device - all panels should refresh
3. Auto-refresh should work every 30 seconds
4. Zoom in on chart - should show more detail
5. Hover on data points - tooltip should appear

### Retention Policy Tests

**Test retention policy is active:**
```sql
-- Check policy configuration
SELECT * FROM timescaledb_information.policy;

-- Verify old data is deleted
-- Create test data from 40 days ago
INSERT INTO telemetry (time, device_id, temperature)
VALUES (NOW() - INTERVAL '40 days', 'test-old', 25.0);

-- Wait for retention job to run (usually every 24h)
-- Or manually trigger:
SELECT run_job(1);

-- Check if old data still exists
SELECT COUNT(*) FROM telemetry WHERE device_id = 'test-old';
-- Expected: 0 (or 1 if job hasn't run yet)
```

### Continuous Aggregate Tests

**Test automatic refresh:**
```sql
-- Create fresh data
INSERT INTO telemetry (time, device_id, temperature)
VALUES (NOW(), 'tank1', 25.0),
       (NOW() + INTERVAL '5 minutes', 'tank1', 26.0);

-- Check if hourly aggregate includes new data
SELECT * FROM telemetry_hourly 
WHERE device_id = 'tank1' 
  AND hour >= NOW() - INTERVAL '1 hour'
ORDER BY hour DESC;
```

### Debugging Commands

**Check backend logs:**
```bash
docker-compose logs -f backend | grep telemetry
```

**Check MQTT messages:**
```bash
mosquitto_sub -h localhost -u tankctl -P password \
  -t 'tankctl/+/telemetry' -v
```

**Check database activity:**
```sql
-- Active queries
SELECT query FROM pg_stat_statements ORDER BY calls DESC LIMIT 5;

-- Slow queries
SELECT query, mean_exec_time FROM pg_stat_statements 
WHERE mean_exec_time > 100 
ORDER BY mean_exec_time DESC;
```

**Check table statistics:**
```sql
SELECT 
  schemaname,
  tablename,
  n_live_tup as live_rows,
  n_dead_tup as dead_rows,
  last_vacuum,
  last_analyze
FROM pg_stat_user_tables 
WHERE tablename IN ('telemetry', 'telemetry_hourly');
```

### Cleanup

**Clear test data:**
```sql
-- Delete all telemetry for device
DELETE FROM telemetry WHERE device_id = 'tank1';

-- Or delete by time range
DELETE FROM telemetry WHERE time < NOW() - INTERVAL '1 day';

-- Verify deletion
SELECT COUNT(*) FROM telemetry;
```

**Reset database:**
```bash
# Drop and recreate TimescaleDB
docker-compose down timescaledb
docker volume rm tankctl_timescaledb-data

docker-compose up -d timescaledb
docker-compose exec timescaledb wait-for-it

# Re-run migration
psql postgresql://tankctl:password@localhost:5432/tankctl_telemetry < migrations/001_create_telemetry_table.sql
```

### Checklist

- [ ] Migration runs without errors
- [ ] Hypertable created successfully
- [ ] Retention policy active
- [ ] Continuous aggregate refreshing
- [ ] MQTT telemetry ingested
- [ ] Data appears in database
- [ ] API endpoints respond correctly
- [ ] All metrics retrieved individually
- [ ] Hourly summaries calculated
- [ ] Grafana dashboard loads
- [ ] Dashboard panels show data
- [ ] Device selector works
- [ ] Time range filtering works
- [ ] Auto-refresh works
- [ ] Retention policy removes old data
- [ ] Load test completes successfully
- [ ] Query performance acceptable
