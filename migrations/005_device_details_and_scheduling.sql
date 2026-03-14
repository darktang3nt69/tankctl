-- Migration: Add device details and scheduling tables
-- Date: 2026-03-15
-- Purpose: Support device metadata, light scheduling, water change scheduling

-- Add columns to devices table
ALTER TABLE devices ADD COLUMN IF NOT EXISTS device_name VARCHAR(100);
ALTER TABLE devices ADD COLUMN IF NOT EXISTS location VARCHAR(100);
ALTER TABLE devices ADD COLUMN IF NOT EXISTS icon_type VARCHAR(50) DEFAULT 'fish_bowl';
ALTER TABLE devices ADD COLUMN IF NOT EXISTS description TEXT;

-- Create light_schedule table
CREATE TABLE IF NOT EXISTS light_schedules (
  id SERIAL PRIMARY KEY,
  device_id VARCHAR(50) NOT NULL,
  enabled BOOLEAN DEFAULT true,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
  UNIQUE(device_id)
);

-- Create water_schedule table
CREATE TABLE IF NOT EXISTS water_schedules (
  id SERIAL PRIMARY KEY,
  device_id VARCHAR(50) NOT NULL,
  schedule_type VARCHAR(20) NOT NULL, -- 'weekly', 'custom'
  day_of_week INTEGER, -- 0-6 for weekly schedules (0=Sunday)
  schedule_date DATE, -- For custom schedules
  schedule_time TIME NOT NULL DEFAULT '12:00:00',
  notes TEXT,
  completed BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

-- Create indices for faster queries
CREATE INDEX IF NOT EXISTS idx_water_schedules_device_id ON water_schedules(device_id);
CREATE INDEX IF NOT EXISTS idx_water_schedules_schedule_date ON water_schedules(schedule_date);
CREATE INDEX IF NOT EXISTS idx_light_schedules_device_id ON light_schedules(device_id);
