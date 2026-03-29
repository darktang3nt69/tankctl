-- Migration 011: Add notification preference columns to water_schedules table
-- Purpose: Support granular user control over water schedule reminder timing
-- Columns:
--   notify_24h: Boolean - send reminder 24 hours before scheduled time
--   notify_1h: Boolean - send reminder 1 hour before scheduled time
--   notify_on_time: Boolean - send reminder at scheduled time

ALTER TABLE water_schedules
    ADD COLUMN IF NOT EXISTS notify_24h BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS notify_1h BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS notify_on_time BOOLEAN NOT NULL DEFAULT TRUE;

-- Ensure all existing schedules have these notification preferences enabled by default
-- (This is a no-op if columns already exist with DEFAULT TRUE)
UPDATE water_schedules
SET notify_24h = TRUE,
    notify_1h = TRUE,
    notify_on_time = TRUE
WHERE notify_24h IS NULL
   OR notify_1h IS NULL
   OR notify_on_time IS NULL;
