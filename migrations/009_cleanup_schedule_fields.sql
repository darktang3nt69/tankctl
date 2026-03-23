-- Migration: Clean up water schedule fields based on schedule_type
-- Purpose: Ensure weekly schedules have NULL schedule_date, custom schedules have NULL days_of_week

-- For weekly schedules, clear schedule_date
UPDATE water_schedules
SET schedule_date = NULL
WHERE schedule_type = 'weekly' AND schedule_date IS NOT NULL;

-- For custom schedules, clear days_of_week
UPDATE water_schedules
SET days_of_week = NULL
WHERE schedule_type = 'custom' AND days_of_week IS NOT NULL;
