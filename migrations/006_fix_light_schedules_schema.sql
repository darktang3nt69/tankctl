-- Migration: Fix light_schedules table schema
-- Date: 2026-03-15
-- Purpose: Rename start_time/end_time columns to on_time/off_time for light_schedules table

-- Check if table exists before attempting migration
DO $$ 
BEGIN
  -- Only rename columns if they still have the old names
  IF EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name='light_schedules' AND column_name='start_time'
  ) THEN
    ALTER TABLE light_schedules RENAME COLUMN start_time TO on_time;
    ALTER TABLE light_schedules RENAME COLUMN end_time TO off_time;
    RAISE NOTICE 'Successfully renamed light_schedules columns: start_time→on_time, end_time→off_time';
  ELSE
    RAISE NOTICE 'Column rename already applied or table structure different - skipping';
  END IF;
END $$;
