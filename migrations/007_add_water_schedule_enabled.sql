-- Migration 007: Add enabled flag and reminder tracking to water_schedules
ALTER TABLE water_schedules
    ADD COLUMN IF NOT EXISTS enabled BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS last_reminder_sent_at TIMESTAMP WITH TIME ZONE;
