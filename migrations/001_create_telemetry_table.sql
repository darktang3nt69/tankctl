-- TankCtl Telemetry Table Migration
-- Creates basic telemetry table for storing device telemetry data
-- TimescaleDB extensions are optional and applied separately

-- Create telemetry table with proper timestamps
CREATE TABLE IF NOT EXISTS telemetry (
    time TIMESTAMPTZ NOT NULL,
    device_id TEXT NOT NULL,
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    pressure DOUBLE PRECISION,
    metadata JSONB
);

-- Create composite index for efficient device + time queries
CREATE INDEX IF NOT EXISTS idx_telemetry_device_time
ON telemetry (device_id, time DESC);

-- Create index on temperature for analytics queries
CREATE INDEX IF NOT EXISTS idx_telemetry_temperature
ON telemetry (device_id, temperature) WHERE temperature IS NOT NULL;

-- Create index on humidity for analytics queries
CREATE INDEX IF NOT EXISTS idx_telemetry_humidity
ON telemetry (device_id, humidity) WHERE humidity IS NOT NULL;
