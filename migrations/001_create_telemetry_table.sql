-- TankCtl Telemetry Table Migration
-- Creates TimescaleDB hypertable for storing device telemetry data

-- Create telemetry table with proper timestamps
CREATE TABLE IF NOT EXISTS telemetry (
    time TIMESTAMPTZ NOT NULL,
    device_id TEXT NOT NULL,
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    pressure DOUBLE PRECISION,
    metadata JSONB
);

-- Convert to TimescaleDB hypertable (required for efficient time-series queries)
-- This partitions data by time and device_id for parallelized scans
SELECT create_hypertable('telemetry', 'time', if_not_exists => TRUE);

-- Create composite index for efficient device + time queries
CREATE INDEX IF NOT EXISTS idx_telemetry_device_time
ON telemetry (device_id, time DESC);

-- Create index on temperature for analytics queries
CREATE INDEX IF NOT EXISTS idx_telemetry_temperature
ON telemetry (device_id, temperature) WHERE temperature IS NOT NULL;

-- Create index on humidity for analytics queries
CREATE INDEX IF NOT EXISTS idx_telemetry_humidity
ON telemetry (device_id, humidity) WHERE humidity IS NOT NULL;

-- Add retention policy: keep only last 30 days of data
-- This automatically deletes old data to save storage
SELECT add_retention_policy('telemetry', INTERVAL '30 days', if_not_exists => TRUE);

-- Create continuous aggregate for hourly rollups (for dashboards)
-- This pre-aggregates data hourly for faster dashboard queries
CREATE MATERIALIZED VIEW IF NOT EXISTS telemetry_hourly AS
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
GROUP BY hour, device_id
WITH DATA;

-- Refresh the continuous aggregate automatically every hour
SELECT add_continuous_aggregate_policy('telemetry_hourly',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '30 minutes',
    if_not_exists => TRUE);

-- Create index on hourly view for dashboard queries
CREATE INDEX IF NOT EXISTS idx_telemetry_hourly_device_time
ON telemetry_hourly (device_id, hour DESC);
