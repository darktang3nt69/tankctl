## Telemetry Pipeline Implementation

The TankCtl telemetry pipeline ingests device metrics and stores them efficiently in TimescaleDB for time-series analysis and visualization.

### Architecture Overview

```
Device (MQTT)
    ↓
    └→ tankctl/{device_id}/telemetry
        ↓
        MQTT Broker (Mosquitto)
        ↓
        TankCtl Backend
        ├→ TelemetryHandler (extracts device_id, channel)
        ├→ TelemetryService (validates metrics)
        ├→ TelemetryRepository (stores to TimescaleDB)
        ↓
        TimescaleDB
        ├→ telemetry table (raw data)
        ├→ telemetry_hourly continuous aggregate (rolled up)
        └→ Retention policy (30 days)
        ↓
        Grafana (dashboards)
```

### Data Flow

**1. Device publishes telemetry:**
```
Device → MQTT Topic: tankctl/tank1/telemetry
Payload:
{
    "temperature": 24.5,
    "humidity": 65.2,
    "pressure": 1013.25,
    "metadata": {"location": "sensor_1"}
}
```

**2. Backend receives and routes:**
- MQTT client extracts `device_id` = "tank1" from topic
- Routes to `TelemetryHandler`
- Handler passes to `TelemetryService`

**3. Service validates and stores:**
- Validates numeric values
- Converts to float
- Calls `TelemetryRepository.insert()`
- Logs event

**4. Repository writes to TimescaleDB:**
- Uses raw SQL for direct insertion
- Records timestamp (NOW() UTC)
- Stores all metrics and metadata

**5. Continuous aggregates update:**
- Hourly rollup automatically calculated
- Pre-aggregated data available for dashboards

**6. Grafana queries data:**
- Fetches raw or aggregated data
- Displays on dashboard
- Updates every 30 seconds

### TimescaleDB Schema

**Main table: `telemetry`**
```sql
CREATE TABLE telemetry (
    time TIMESTAMPTZ NOT NULL,        -- Timestamp (time-series key)
    device_id TEXT NOT NULL,          -- Device identifier
    temperature DOUBLE PRECISION,      -- Temperature in °C
    humidity DOUBLE PRECISION,         -- Humidity in %
    pressure DOUBLE PRECISION,         -- Pressure in hPa
    metadata JSONB                     -- Additional metadata as JSON
);

-- Hypertable: automatically partitions by time
SELECT create_hypertable('telemetry', 'time');

-- Indexes for query performance
CREATE INDEX idx_telemetry_device_time ON telemetry (device_id, time DESC);
CREATE INDEX idx_telemetry_temperature ON telemetry (device_id, temperature) WHERE temperature IS NOT NULL;
CREATE INDEX idx_telemetry_humidity ON telemetry (device_id, humidity) WHERE humidity IS NOT NULL;
```

**Continuous aggregate: `telemetry_hourly`**
```sql
CREATE MATERIALIZED VIEW telemetry_hourly AS
SELECT
    time_bucket('1 hour', time) as hour,
    device_id,
    AVG(temperature) as temp_avg,
    MAX(temperature) as temp_max,
    MIN(temperature) as temp_min,
    AVG(humidity) as humidity_avg,
    MAX(humidity) as humidity_max,
    MIN(humidity) as humidity_min,
    COUNT(*) as sample_count
FROM telemetry
GROUP BY hour, device_id;
```

**Retention policy:**
```sql
-- Keep only 30 days of data
SELECT add_retention_policy('telemetry', INTERVAL '30 days');
```

### API Endpoints

#### Get Recent Telemetry
```
GET /devices/{device_id}/telemetry?limit=100&hours=24

Query Parameters:
- limit: Max records (1-10000, default 100)
- hours: Time window in hours (optional)

Response:
{
    "device_id": "tank1",
    "count": 10,
    "data": [
        {
            "time": "2025-01-15T10:30:00+00:00",
            "device_id": "tank1",
            "temperature": 24.5,
            "humidity": 65.2,
            "pressure": 1013.25,
            "metadata": null
        }
    ]
}
```

#### Get Specific Metric
```
GET /devices/{device_id}/telemetry/{metric}?limit=100

Path Parameters:
- metric: 'temperature', 'humidity', or 'pressure'

Query Parameters:
- limit: Max records (1-10000, default 100)

Response:
{
    "device_id": "tank1",
    "metric": "temperature",
    "count": 10,
    "data": [
        {
            "time": "2025-01-15T10:30:00+00:00",
            "device_id": "tank1",
            "value": 24.5
        }
    ]
}
```

#### Get Hourly Summary
```
GET /devices/{device_id}/telemetry/hourly/summary?hours=24

Query Parameters:
- hours: Number of hours (1-8760, default 24)

Response:
{
    "device_id": "tank1",
    "count": 24,
    "data": [
        {
            "hour": "2025-01-14T10:00:00+00:00",
            "device_id": "tank1",
            "temperature": {
                "avg": 24.2,
                "max": 25.1,
                "min": 23.5
            },
            "humidity": {
                "avg": 63.5,
                "max": 68.2,
                "min": 60.1
            },
            "sample_count": 120
        }
    ]
}
```

### Repository Layer

**TelemetryRepository** in `src/repository/telemetry_repository.py`

Methods:
- `insert(device_id, temperature, humidity, pressure, metadata)` - Store data point
- `get_recent(device_id, limit, hours)` - Retrieve recent data
- `get_by_metric(device_id, metric, limit)` - Get specific metric
- `get_hourly_rollup(device_id, hours)` - Get aggregated hourly data

**Implementation details:**
- Uses raw SQL with `text()` for direct TimescaleDB access
- Handles NULL values gracefully
- Uses UTC timestamps
- Validates metric names

### Service Layer

**TelemetryService** in `src/services/telemetry_service.py`

Methods:
- `store_telemetry(device_id, payload)` - Parse and store device telemetry
- `get_device_telemetry(device_id, metric_name, limit, hours)` - Retrieve telemetry
- `get_hourly_summary(device_id, hours)` - Get aggregated data

**Validation:**
- Ensures at least one metric is present
- Converts values to float
- Logs all operations
- Handles errors gracefully

### MQTT Integration

**TelemetryHandler** in `src/infrastructure/mqtt/handlers.py`

```python
class TelemetryHandler(MessageHandler):
    def handle(self, device_id: str, payload: dict) -> None:
        # Store in TimescaleDB
        service.store_telemetry(device_id, payload)
        
        # Also mark device as online (heartbeat)
        device_service.handle_heartbeat(device_id)
```

**Message routing:**
- Topic: `tankctl/{device_id}/telemetry`
- Channel: `telemetry`
- Routed by MQTT client via handler registry

### Grafana Dashboard

**Location:** `grafana/dashboards/tankctl-telemetry-dashboard.json`

**Panels:**
1. **Temperature Over Time** - Line chart of temperature readings
2. **Humidity Over Time** - Line chart of humidity readings
3. **Temperature Statistics** - 24h min/max/avg pie chart
4. **Current Temperature** - Stat panel with current value
5. **Current Humidity** - Stat panel with current value

**Dashboard features:**
- Device selector dropdown (auto-populated from DB)
- 24-hour default time range
- Auto-refresh every 30 seconds
- All panels use TimescaleDB queries
- Color-coded thresholds

**Sample Grafana Queries:**

Get raw temperature data:
```sql
SELECT
  time,
  temperature as temperature
FROM telemetry
WHERE device_id = '${deviceId}' AND temperature IS NOT NULL
ORDER BY time DESC
LIMIT 1000
```

Get hourly aggregates:
```sql
SELECT
  hour,
  temp_avg,
  temp_max,
  temp_min
FROM telemetry_hourly
WHERE device_id = '${deviceId}'
  AND hour > NOW() - INTERVAL '24 hours'
ORDER BY hour DESC
```

### Configuration

**Environment Variables:**
```bash
# TimescaleDB
TIMESCALE_HOST=localhost
TIMESCALE_PORT=5432
TIMESCALE_DB=tankctl_telemetry
TIMESCALE_USER=tankctl
TIMESCALE_PASSWORD=password
```

**Database Connection:**
`postgresql://tankctl:password@localhost:5432/tankctl_telemetry`

### Migration & Setup

**Run migration:**
```bash
# Connect to TimescaleDB
psql postgresql://tankctl:password@localhost:5432/tankctl_telemetry

# Execute migration
\i migrations/001_create_telemetry_table.sql
```

**Verify setup:**
```sql
-- Check table exists and is hypertable
SELECT hypertable_name FROM timescaledb_information.hypertables;

-- Check indexes
SELECT indexname FROM pg_indexes WHERE tablename = 'telemetry';

-- Check retention policy
SELECT * FROM timescaledb_information.policy;

-- Check continuous aggregate
SELECT * FROM timescaledb_information.continuous_aggregates;
```

### Performance Characteristics

**Write Performance:**
- ~10,000 inserts/second per partition
- Batching recommended for bulk loads
- Automatic compression after a certain age

**Query Performance:**
- Device + time range: Sub-millisecond via index
- Hourly aggregates: Pre-computed, instant retrieval
- Full table scans: Optimized by hypertable partitioning

**Storage:**
- Raw data: ~100-200 bytes per point
- Compression: ~50% space savings after age threshold
- Retention: Automatic deletion after 30 days

### Testing

**Manual test:**
```bash
# Publish test telemetry
mosquitto_pub -h localhost -u tankctl -P password \
  -t "tankctl/tank1/telemetry" \
  -m '{"temperature": 24.5, "humidity": 65.2, "pressure": 1013.25}'

# Query via API
curl http://localhost:8000/devices/tank1/telemetry

# Query via SQL
psql postgresql://tankctl:password@localhost:5432/tankctl_telemetry
SELECT * FROM telemetry WHERE device_id='tank1' ORDER BY time DESC LIMIT 10;
```

**Bulk load test:**
```python
import requests
import json

for i in range(1000):
    payload = {
        "temperature": 20 + (i % 10),
        "humidity": 60 + (i % 20)
    }
    requests.post(
        "http://localhost:8000/devices/tank1/telemetry",
        json=payload
    )
```

### Troubleshooting

**No data appearing:**
1. Check MQTT broker is running: `docker-compose ps | grep mosquitto`
2. Verify device publishes to correct topic
3. Check backend logs: `docker-compose logs -f backend`
4. Verify TimescaleDB connection: `docker-compose exec timescaledb psql`

**Slow queries:**
1. Check index exists: `SELECT * FROM pg_stat_user_indexes WHERE relname='telemetry'`
2. Run `ANALYZE telemetry` to update statistics
3. Check for missing retention policy

**High storage:**
1. Verify retention policy is active
2. Check data size: `SELECT pg_size_pretty(pg_total_relation_size('telemetry'))`
3. Enable compression: `SELECT compress_chunk(chunk) FROM show_chunks('telemetry')`

### Best Practices

1. **Device Publishing:**
   - Always include at least one metric
   - Use valid numeric values
   - Include timestamp in metadata if needed
   - Publish at consistent intervals

2. **Frontend/API:**
   - Use reasonable limits (default 100)
   - Filter by time range when possible
   - Cache hourly summaries for dashboards
   - Use metric-specific queries over full telemetry

3. **Grafana:**
   - Use continuous aggregate queries for performance
   - Set appropriate refresh intervals
   - Use time range filters effectively
   - Archive old dashboards

4. **Database:**
   - Monitor chunk size and compression
   - Review retention policy periodically
   - Backup before major changes
   - Monitor query performance regularly
