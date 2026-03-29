import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Global notification preferences for water schedules.
///
/// Settings stored in SharedPreferences with keys:
/// - water_schedule_notify_24h
/// - water_schedule_notify_1h
/// - water_schedule_notify_on_time
///
/// These settings apply to all water schedules by default.
/// Per-schedule settings in tank_detail override these globals.
class NotificationPreferencesScreen extends ConsumerStatefulWidget {
  const NotificationPreferencesScreen({super.key});

  @override
  ConsumerState<NotificationPreferencesScreen> createState() =>
      _NotificationPreferencesScreenState();
}

class _NotificationPreferencesScreenState
    extends ConsumerState<NotificationPreferencesScreen> {
  late bool _notify24h;
  late bool _notify1h;
  late bool _notifyOnTime;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadPreferences();
  }

  /// Load preferences from SharedPreferences.
  Future<void> _loadPreferences() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      setState(() {
        _notify24h = prefs.getBool('water_schedule_notify_24h') ?? true;
        _notify1h = prefs.getBool('water_schedule_notify_1h') ?? true;
        _notifyOnTime = prefs.getBool('water_schedule_notify_on_time') ?? true;
        _loading = false;
      });
    } catch (e) {
      if (mounted) {
        setState(() => _loading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load preferences: $e')),
        );
      }
    }
  }

  /// Save preferences to SharedPreferences.
  Future<void> _savePreferences() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await Future.wait([
        prefs.setBool('water_schedule_notify_24h', _notify24h),
        prefs.setBool('water_schedule_notify_1h', _notify1h),
        prefs.setBool('water_schedule_notify_on_time', _notifyOnTime),
      ]);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Row(
              children: [
                Icon(Icons.check_circle, color: Colors.white),
                SizedBox(width: 12),
                Text('Notification preferences saved'),
              ],
            ),
            backgroundColor: Colors.green,
            duration: Duration(seconds: 2),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to save preferences: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('Notification Preferences'),
          centerTitle: false,
        ),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Notification Preferences'),
        centerTitle: false,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Water Schedule Notifications',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'These global settings apply to all water schedules. '
                'You can customize notifications for individual schedules in tank details.',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.grey[600],
                ),
              ),
              const SizedBox(height: 24),

              // 24h before notification
              _buildPreferenceCard(
                context,
                title: 'Notify 24 Hours Before',
                subtitle: 'Receive a reminder one day before scheduled water change',
                value: _notify24h,
                onChanged: (value) => setState(() {
                  _notify24h = value;
                  _savePreferences();
                }),
              ),
              const SizedBox(height: 12),

              // 1h before notification
              _buildPreferenceCard(
                context,
                title: 'Notify 1 Hour Before',
                subtitle: 'Receive a reminder one hour before scheduled water change',
                value: _notify1h,
                onChanged: (value) => setState(() {
                  _notify1h = value;
                  _savePreferences();
                }),
              ),
              const SizedBox(height: 12),

              // On-time notification
              _buildPreferenceCard(
                context,
                title: 'Notify at Scheduled Time',
                subtitle: 'Receive a reminder at the exact time of scheduled water change',
                value: _notifyOnTime,
                onChanged: (value) => setState(() {
                  _notifyOnTime = value;
                  _savePreferences();
                }),
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// Build a preference card with toggle switch.
  Widget _buildPreferenceCard(
    BuildContext context, {
    required String title,
    required String subtitle,
    required bool value,
    required ValueChanged<bool> onChanged,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.withValues(alpha: 0.2)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 16),
          Switch(
            value: value,
            onChanged: onChanged,
          ),
        ],
      ),
    );
  }
}
