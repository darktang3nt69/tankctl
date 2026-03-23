-- Migration: Create device_push_tokens table for FCM/device push tokens

CREATE TABLE IF NOT EXISTS device_push_tokens (
    id SERIAL PRIMARY KEY,
    device_id TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    platform TEXT NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_device_push_tokens_device_id
    ON device_push_tokens (device_id);
