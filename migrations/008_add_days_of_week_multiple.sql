-- Migration: Support multiple weekdays per water schedule
-- Replaces single day_of_week with days_of_week (comma-separated string)

-- Step 1: Add the new days_of_week column if it doesn't exist
ALTER TABLE water_schedules
ADD COLUMN IF NOT EXISTS days_of_week VARCHAR(20) NULL;

-- Step 2 & 3: If day_of_week column exists, migrate data and drop it
DO $$
BEGIN
  IF EXISTS(SELECT 1 FROM information_schema.columns 
            WHERE table_name='water_schedules' AND column_name='day_of_week') THEN
    -- Migrate existing data: convert single int to comma-separated string
    UPDATE water_schedules
    SET days_of_week = CAST(day_of_week AS VARCHAR)
    WHERE day_of_week IS NOT NULL 
      AND schedule_type = 'weekly'
      AND (days_of_week IS NULL OR days_of_week = '');

    -- Drop old column
    ALTER TABLE water_schedules DROP COLUMN day_of_week;
  END IF;
END;
$$;
