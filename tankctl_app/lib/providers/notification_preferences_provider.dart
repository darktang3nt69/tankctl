/// Notification preferences provider for Riverpod state management
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

// ============================================================================
// State Models
// ============================================================================

/// Global notification preferences for water schedules
class NotificationPreferences {
  final bool notify24h;
  final bool notify1h;
  final bool notifyOnTime;

  const NotificationPreferences({
    this.notify24h = true,
    this.notify1h = true,
    this.notifyOnTime = true,
  });

  /// Create a copy with optional overrides
  NotificationPreferences copyWith({
    bool? notify24h,
    bool? notify1h,
    bool? notifyOnTime,
  }) {
    return NotificationPreferences(
      notify24h: notify24h ?? this.notify24h,
      notify1h: notify1h ?? this.notify1h,
      notifyOnTime: notifyOnTime ?? this.notifyOnTime,
    );
  }

  /// Convert to JSON for persistence
  Map<String, bool> toJson() => {
    'notify_24h': notify24h,
    'notify_1h': notify1h,
    'notify_on_time': notifyOnTime,
  };

  /// Create from JSON
  factory NotificationPreferences.fromJson(Map<String, bool> json) {
    return NotificationPreferences(
      notify24h: json['notify_24h'] ?? true,
      notify1h: json['notify_1h'] ?? true,
      notifyOnTime: json['notify_on_time'] ?? true,
    );
  }
}

// ============================================================================
// State Notifier
// ============================================================================

/// State notifier for managing global notification preferences
/// Auto-persists to SharedPreferences on change
class NotificationPreferencesNotifier
    extends StateNotifier<NotificationPreferences> {
  SharedPreferences? _prefs;

  NotificationPreferencesNotifier()
      : super(const NotificationPreferences());

  /// Initialize by loading from SharedPreferences
  Future<void> initialize() async {
    try {
      _prefs ??= await SharedPreferences.getInstance();
      
      final notify24h = _prefs?.getBool('water_schedule_notify_24h') ?? true;
      final notify1h = _prefs?.getBool('water_schedule_notify_1h') ?? true;
      final notifyOnTime = _prefs?.getBool('water_schedule_notify_on_time') ?? true;

      state = NotificationPreferences(
        notify24h: notify24h,
        notify1h: notify1h,
        notifyOnTime: notifyOnTime,
      );
    } catch (e) {
      // Log error but don't crash - use defaults
    }
  }

  /// Update 24h notification preference and persist
  Future<void> updateNotify24h(bool value) async {
    state = state.copyWith(notify24h: value);
    try {
      _prefs ??= await SharedPreferences.getInstance();
      await _prefs?.setBool('water_schedule_notify_24h', value);
    } catch (e) {
      // Silently fail - preferences will use in-memory state
    }
  }

  /// Update 1h notification preference and persist
  Future<void> updateNotify1h(bool value) async {
    state = state.copyWith(notify1h: value);
    try {
      _prefs ??= await SharedPreferences.getInstance();
      await _prefs?.setBool('water_schedule_notify_1h', value);
    } catch (e) {
      // Silently fail - preferences will use in-memory state
    }
  }

  /// Update on-time notification preference and persist
  Future<void> updateNotifyOnTime(bool value) async {
    state = state.copyWith(notifyOnTime: value);
    try {
      _prefs ??= await SharedPreferences.getInstance();
      await _prefs?.setBool('water_schedule_notify_on_time', value);
    } catch (e) {
      // Silently fail - preferences will use in-memory state
    }
  }
}

// ============================================================================
// Providers
// ============================================================================

/// Provider for global notification preferences
/// Auto-loaded from SharedPreferences on app start
final notificationPreferencesProvider =
    StateNotifierProvider<NotificationPreferencesNotifier, NotificationPreferences>(
  (ref) {
    final notifier = NotificationPreferencesNotifier();
    // Initialize from SharedPreferences
    notifier.initialize();
    return notifier;
  },
);


