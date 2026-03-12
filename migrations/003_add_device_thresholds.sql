-- Add per-device temperature thresholds (nullable) for dashboard/chart rendering.
ALTER TABLE devices
    ADD COLUMN IF NOT EXISTS temp_threshold_low DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS temp_threshold_high DOUBLE PRECISION;
