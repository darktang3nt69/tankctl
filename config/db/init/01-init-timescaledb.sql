-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Task 2.1: Create Metrics Table (Hypertable: tank_metrics)
CREATE TABLE IF NOT EXISTS tank_metrics (
    time        TIMESTAMPTZ       NOT NULL,
    tank_id     UUID              NOT NULL,
    metric      TEXT              NOT NULL,
    value       DOUBLE PRECISION  NOT NULL
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM timescaledb_information.hypertables WHERE hypertable_name = 'tank_metrics'
    ) THEN
        PERFORM create_hypertable('tank_metrics', 'time', if_not_exists => TRUE);
    END IF;
END$$;

-- Task 2.2: Create Status Logs Hypertable
CREATE TABLE IF NOT EXISTS status_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tank_id UUID NOT NULL,
    temperature DOUBLE PRECISION,
    ph DOUBLE PRECISION,
    light_state BOOLEAN,
    firmware_version TEXT,
    timestamp TIMESTAMPTZ NOT NULL
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM timescaledb_information.hypertables WHERE hypertable_name = 'status_logs'
    ) THEN
        PERFORM create_hypertable('status_logs', 'timestamp', if_not_exists => TRUE);
    END IF;
END$$;

-- Task 2.4: Create Schedule Logs Hypertable
CREATE TABLE IF NOT EXISTS tank_schedule_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tank_id UUID NOT NULL,
    event_type TEXT NOT NULL,
    trigger_source TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM timescaledb_information.hypertables WHERE hypertable_name = 'tank_schedule_log'
    ) THEN
        PERFORM create_hypertable('tank_schedule_log', 'timestamp', if_not_exists => TRUE);
    END IF;
END$$;

-- Task 2.5: Indexing
CREATE INDEX IF NOT EXISTS idx_status_logs_tank_id_timestamp ON status_logs (tank_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tank_schedule_log_tank_id_timestamp ON tank_schedule_log (tank_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tank_commands_tank_id_status ON tank_commands (tank_id, status);
CREATE INDEX IF NOT EXISTS idx_tank_commands_status_created_at ON tank_commands (status, created_at DESC);

-- Task 3: Continuous Aggregates and Retention Policies

-- 3.1: Hourly Aggregate
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

-- 3.2: Daily Aggregate
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

-- 3.3: 5-minute Aggregate
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

-- 3.4: Continuous Aggregate Policies
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

-- 3.5: Retention Policies
SELECT add_retention_policy('status_logs', INTERVAL '30 days', if_not_exists => TRUE);
SELECT add_retention_policy('tank_commands', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('tank_schedule_log', INTERVAL '90 days', if_not_exists => TRUE);
  