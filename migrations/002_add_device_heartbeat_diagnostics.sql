-- Migration: Add heartbeat diagnostic fields to devices table
-- Adds uptime_ms, rssi, and wifi_status columns populated from device heartbeat payloads.

ALTER TABLE devices
    ADD COLUMN IF NOT EXISTS uptime_ms INTEGER,
    ADD COLUMN IF NOT EXISTS rssi INTEGER,
    ADD COLUMN IF NOT EXISTS wifi_status VARCHAR(50);
