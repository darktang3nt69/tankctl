-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Example: create a metrics table and hypertable
CREATE TABLE IF NOT EXISTS tank_metrics (
    time        TIMESTAMPTZ       NOT NULL,
    tank_id     UUID              NOT NULL,
    metric      TEXT              NOT NULL,
    value       DOUBLE PRECISION  NOT NULL
);

SELECT create_hypertable('tank_metrics', 'time', if_not_exists => TRUE);

-- Task 2.2: Create Status Logs Hypertable
CREATE TABLE IF NOT EXISTS status_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tank_id UUID NOT NULL,
    temperature DOUBLE PRECISION,
    ph DOUBLE PRECISION,
    light_state BOOLEAN,
    firmware_version VARCHAR,
    timestamp TIMESTAMPTZ NOT NULL
);

SELECT create_hypertable('status_logs', 'timestamp', if_not_exists => TRUE);

-- Task 2.4: Create Schedule Logs Hypertable
CREATE TABLE IF NOT EXISTS tank_schedule_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tank_id UUID NOT NULL,
    event_type VARCHAR NOT NULL,
    trigger_source VARCHAR NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL
);

SELECT create_hypertable('tank_schedule_log', 'timestamp', if_not_exists => TRUE);

-- Task 2.5: Indexing considerations
-- TimescaleDB automatically indexes the time column for hypertables.
-- Consider adding indexes on tank_id for faster queries filtering by tank.
-- CREATE INDEX IF NOT EXISTS idx_status_logs_tank_id ON status_logs (tank_id, timestamp DESC);
-- CREATE INDEX IF NOT EXISTS idx_tank_schedule_log_tank_id ON tank_schedule_log (tank_id, timestamp DESC);
-- Documentation would typically involve describing the schema and query patterns.

-- Task 3: Implement Continuous Aggregates and Retention Policies

-- Task 3.1: Implement Hourly Temperature Continuous Aggregates
-- Task 3.2: Implement Daily Temperature Continuous Aggregates
-- Task 3.3: Implement pH Continuous Aggregates
-- Assuming hourly for pH for now, adjust if needed.

CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_status_aggregates
WITH (timescaledb.continuous)
AS
SELECT
    time_bucket('1 hour', timestamp) AS time,
    tank_id,
    AVG(temperature) AS avg_temperature,
    MIN(temperature) AS min_temperature,
    MAX(temperature) AS max_temperature,
    AVG(ph) AS avg_ph,
    MIN(ph) AS min_ph,
    MAX(ph) AS max_ph
FROM status_logs
GROUP BY time_bucket('1 hour', timestamp), tank_id
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS daily_status_aggregates
WITH (timescaledb.continuous)
AS
SELECT
    time_bucket('1 day', timestamp) AS time,
    tank_id,
    AVG(temperature) AS avg_temperature,
    MIN(temperature) AS min_temperature,
    MAX(temperature) AS max_temperature,
    AVG(ph) AS avg_ph,
    MIN(ph) AS min_ph,
    MAX(ph) AS max_ph
FROM status_logs
GROUP BY time_bucket('1 day', timestamp), tank_id
WITH NO DATA;

-- New: 5-minute continuous aggregate
CREATE MATERIALIZED VIEW IF NOT EXISTS five_min_status_aggregates
WITH (timescaledb.continuous)
AS
SELECT
    time_bucket('5 minutes', timestamp) AS time,
    tank_id,
    AVG(temperature) AS avg_temperature,
    MIN(temperature) AS min_temperature,
    MAX(temperature) AS max_temperature,
    AVG(ph) AS avg_ph,
    MIN(ph) AS min_ph,
    MAX(ph) AS max_ph
FROM status_logs
GROUP BY time_bucket('5 minutes', timestamp), tank_id
WITH NO DATA;

-- Task 3.4: Configure Refresh Policies for Aggregates
-- Refresh hourly aggregates more frequently, daily less often.
-- Add refresh policy for 5-minute aggregate
SELECT add_continuous_aggregate_policy('hourly_status_aggregates',
  start_offset => INTERVAL '1 day',
  end_offset => INTERVAL '1 hour',
  schedule_interval => INTERVAL '30 minutes',
  if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('daily_status_aggregates',
  start_offset => INTERVAL '1 month',
  end_offset => INTERVAL '1 day',
  schedule_interval => INTERVAL '1 day',
  if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('five_min_status_aggregates',
  start_offset => INTERVAL '1 hour',
  end_offset => INTERVAL '5 minutes',
  schedule_interval => INTERVAL '1 minute',
  if_not_exists => TRUE);

-- Task 3.5: Implement Retention Policy for Status Logs (30 days)
SELECT add_retention_policy('status_logs', INTERVAL '30 days', if_not_exists => TRUE);

-- Task 3.6: Implement Retention Policies for Commands and Acknowledgments (90 days)
-- Also including schedule logs (90 days) as per Task 3 description.
SELECT add_retention_policy('tank_commands', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('tank_schedule_log', INTERVAL '90 days', if_not_exists => TRUE); 