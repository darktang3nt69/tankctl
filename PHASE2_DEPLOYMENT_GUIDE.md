---
title: PHASE2_DEPLOYMENT_GUIDE
type: note
permalink: tankctl/phase2-deployment-guide
---

# Phase 2 Deployment Guide

## Prerequisites

- TankCtl backend running with PostgreSQL database
- Phase 1 migration must be applied before Phase 2 code deployment

## Deployment Steps

### 1. Database Migration (Phase 1 - First)

Apply migration in PostgreSQL:

```bash
# Connect to tankctl database
psql -U tankctl -h localhost -d tankctl < migrations/011_add_water_schedule_notification_preferences.sql
```

Or using Docker:

```bash
docker exec tankctl-db psql -U tankctl -d tankctl -f /migrations/011_add_water_schedule_notification_preferences.sql
```

Verify migration applied:

```sql
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'water_schedules' AND column_name LIKE 'notify%';
```

Expected output:
```
 column_name │ data_type │ column_default
─────────────┼───────────┼───────────────
 notify_24h  │ boolean   │ true
 notify_1h   │ boolean   │ true
 notify_on_time │ boolean │ true
```

### 2. Code Deployment (Phase 2)

1. **Deploy backend code:**
   ```bash
   # Pull Phase 2 changes
   git pull origin phase-2-notification-preferences
   
   # Install/update dependencies (if any)
   pip install -r requirements.txt
   
   # Restart backend
   docker restart tankctl-backend
   # or
   systemctl restart tankctl-backend
   ```

2. **Verify model changes:**
   ```python
   from src.infrastructure.db.models import WaterScheduleModel
   
   # Check model has notify_* attributes
   assert hasattr(WaterScheduleModel, 'notify_24h')
   assert hasattr(WaterScheduleModel, 'notify_1h')
   assert hasattr(WaterScheduleModel, 'notify_on_time')
   ```

3. **Verify service changes:**
   ```python
   from src.services.water_schedule_reminder_service import WaterScheduleReminderService
   
   service = WaterScheduleReminderService()
   assert hasattr(service, '_is_reminder_enabled')
   ```

### 3. Testing Deployment

Run test suite to verify integration:

```bash
# Run all water schedule tests
pytest tests/test_water_schedule_reminders.py -v

# Run only preference tests
pytest tests/test_water_schedule_reminders.py::TestNotificationPreferencesFiltering -v

# Run with coverage
pytest tests/test_water_schedule_reminders.py --cov=src.services.water_schedule_reminder_service --cov-report=html
```

### 4. Monitor Logs

Watch logs for correct behavior:

```bash
# Tail backend logs
docker logs -f tankctl-backend

# Look for water reminder logs
docker logs tankctl-backend | grep -i "water_reminder"
```

Expected log entries:

```
water_reminder_skipped_preference device_id=tank1 schedule_id=42 reminder_type=day_before preference=notify_24h reason=notify_24h=False

water_reminder_sent device_id=tank1 schedule_id=42 reminder_type=hour_before sent=1
```

### 5. Data Verification

Check existing schedules have defaults:

```sql
SELECT 
  id, 
  device_id, 
  notify_24h, 
  notify_1h, 
  notify_on_time 
FROM water_schedules;
```

All should show: `true | true | true`

### 6. Rollback Plan (if needed)

If Phase 2 needs to be rolled back:

```bash
# 1. Revert code to previous version
git checkout HEAD~1

# 2. Restart backend
docker restart tankctl-backend

# 3. Database migration stays (backward compatible)
# - Old code ignores notify_* columns gracefully
# - No data cleanup needed
```

## Monitoring Checklist

After deployment, verify:

- [ ] Backend starts without errors
- [ ] Database migration applied successfully  
- [ ] Tests pass: `pytest tests/test_water_schedule_reminders.py`
- [ ] Logs show correct reminder behavior
- [ ] Existing schedules with notify_*=TRUE still send reminders
- [ ] New schedules can be created with preference settings
- [ ] FCM notifications include reminder_type in data
- [ ] No increase in error rates

## Performance Considerations

- New index `idx_water_schedules_notifications` improves query performance
- Preference filtering is O(1) - single boolean check per reminder
- No additional database calls required
- Memory footprint unchanged

## Next Steps (Phase 3)

After Phase 2 is stable:

1. Develop API endpoints to manage notify_* preferences
2. Update Flutter mobile app to display preference toggles
3. Add global user notification preferences
4. Implement alert acknowledgment workflow
5. Add notification history tracking

## Troubleshooting

### Issue: "Attribute error: 'WaterScheduleModel' has no attribute 'notify_24h'"

**Solution:** 
- Migration not applied yet - run Step 1 first
- Code not updated - pull latest changes
- Python cache stale - restart Python process

### Issue: Reminders still fire when notify_24h=False

**Solution:**
- Migration applied but model not reloaded - restart backend
- Code not running latest version - verify deployment
- Check logs for correct schedule preference values

### Issue: Logs not showing skipped reminders

**Solution:**
- Logger level might be filtering INFO - check logging config
- Schedule might have all notify_*=TRUE (no skips)
- Check specific device_id: `docker logs | grep device_id=tank1`

## Support

For issues, check:
1. `PHASE2_VERIFICATION_CHECKLIST.md` - Feature completeness
2. `docs/backend/PHASE2_NOTIFICATION_PREFERENCES.md` - Architecture details
3. Test logs: `pytest -vv` output for specific failures
4. Backend logs with `grep water_reminder` filter