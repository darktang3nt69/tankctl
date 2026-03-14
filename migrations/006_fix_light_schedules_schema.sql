-- Migration: Fix light_schedules table schema
-- Date: 2026-03-15
-- Purpose: Add id primary key and normalize column names for light_schedules table

-- Drop the existing light_schedules table with its constraints
DROP TABLE IF EXISTS light_schedules CASCADE;

-- Create light_schedule table with correct schema (using on_time/off_time to match domain model)
CREATE TABLE IF NOT EXISTS light_schedules (
  id SERIAL PRIMARY KEY,
  device_id VARCHAR(50) NOT NULL,
  enabled BOOLEAN DEFAULT true,
  on_time TIME NOT NULL,
  off_time TIME NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
  UNIQUE(device_id)
);

-- Create indices for faster queries
CREATE INDEX IF NOT EXISTS idx_light_schedules_device_id ON light_schedules(device_id);
