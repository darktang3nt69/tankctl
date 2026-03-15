-- Migration: Support multiple weekdays per water schedule
-- Replaces single day_of_week with days_of_week (comma-separated string)

ALTER TABLE water_schedules
RENAME COLUMN day_of_week TO day_of_week_old;

-- New column for comma-separated days (e.g., "1,3,5" for Mon,Wed,Fri)
ALTER TABLE water_schedules
ADD COLUMN days_of_week VARCHAR(20) NULL;

-- Migrate existing data: convert single int to comma-separated string
UPDATE water_schedules
SET days_of_week = CAST(day_of_week_old AS VARCHAR)
WHERE day_of_week_old IS NOT NULL AND schedule_type = 'weekly';

-- Drop old column
ALTER TABLE water_schedules
DROP COLUMN day_of_week_old;
