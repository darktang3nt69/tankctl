/// Tests for notification preferences provider with SharedPreferences persistence
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tankctl_app/providers/notification_preferences_provider.dart';

void main() {
  group('NotificationPreferences', () {
    test('creates with default values', () {
      const prefs = NotificationPreferences();
      expect(prefs.notify24h, true);
      expect(prefs.notify1h, true);
      expect(prefs.notifyOnTime, true);
    });

    test('creates with custom values', () {
      const prefs = NotificationPreferences(
        notify24h: false,
        notify1h: true,
        notifyOnTime: false,
      );
      expect(prefs.notify24h, false);
      expect(prefs.notify1h, true);
      expect(prefs.notifyOnTime, false);
    });

    test('copyWith creates new instance with overrides', () {
      const original = NotificationPreferences(
        notify24h: true,
        notify1h: false,
        notifyOnTime: true,
      );

      final updated = original.copyWith(notify1h: true);

      expect(updated.notify24h, true);
      expect(updated.notify1h, true);
      expect(updated.notifyOnTime, true);
      // Verify original unchanged
      expect(original.notify1h, false);
    });

    test('toJson converts to map', () {
      const prefs = NotificationPreferences(
        notify24h: false,
        notify1h: true,
        notifyOnTime: false,
      );

      final json = prefs.toJson();
      expect(json, {
        'notify_24h': false,
        'notify_1h': true,
        'notify_on_time': false,
      });
    });

    test('fromJson creates from map', () {
      final json = {
        'notify_24h': false,
        'notify_1h': true,
        'notify_on_time': false,
      };

      final prefs = NotificationPreferences.fromJson(json);
      expect(prefs.notify24h, false);
      expect(prefs.notify1h, true);
      expect(prefs.notifyOnTime, false);
    });

    test('fromJson handles missing fields with defaults', () {
      final json = {'notify_24h': false};

      final prefs = NotificationPreferences.fromJson(json);
      expect(prefs.notify24h, false);
      expect(prefs.notify1h, true); // default
      expect(prefs.notifyOnTime, true); // default
    });
  });

  group('NotificationPreferencesNotifier', () {
    setUpAll(() {
      TestWidgetsFlutterBinding.ensureInitialized();
    });

    setUp(() {
      // Clear SharedPreferences before each test
      SharedPreferences.setMockInitialValues({});
    });

    test('initial state has default values', () async {
      final notifier = NotificationPreferencesNotifier();
      expect(notifier.state.notify24h, true);
      expect(notifier.state.notify1h, true);
      expect(notifier.state.notifyOnTime, true);
    });

    test('initialize loads from SharedPreferences', () async {
      // Set up mock SharedPreferences with saved values
      SharedPreferences.setMockInitialValues({
        'water_schedule_notify_24h': false,
        'water_schedule_notify_1h': true,
        'water_schedule_notify_on_time': false,
      });

      final notifier = NotificationPreferencesNotifier();
      await notifier.initialize();

      expect(notifier.state.notify24h, false);
      expect(notifier.state.notify1h, true);
      expect(notifier.state.notifyOnTime, false);
    });

    test('initialize uses defaults when SharedPreferences is empty', () async {
      final notifier = NotificationPreferencesNotifier();
      await notifier.initialize();

      expect(notifier.state.notify24h, true);
      expect(notifier.state.notify1h, true);
      expect(notifier.state.notifyOnTime, true);
    });

    test('updateNotify24h changes state and persists', () async {
      final notifier = NotificationPreferencesNotifier();
      await notifier.initialize();

      await notifier.updateNotify24h(false);

      expect(notifier.state.notify24h, false);

      // Verify persisted to SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getBool('water_schedule_notify_24h'), false);
    });

    test('updateNotify1h changes state and persists', () async {
      final notifier = NotificationPreferencesNotifier();
      await notifier.initialize();

      await notifier.updateNotify1h(false);

      expect(notifier.state.notify1h, false);

      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getBool('water_schedule_notify_1h'), false);
    });

    test('updateNotifyOnTime changes state and persists', () async {
      final notifier = NotificationPreferencesNotifier();
      await notifier.initialize();

      await notifier.updateNotifyOnTime(false);

      expect(notifier.state.notifyOnTime, false);

      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getBool('water_schedule_notify_on_time'), false);
    });

    test('multiple updates persist correctly', () async {
      final notifier = NotificationPreferencesNotifier();
      await notifier.initialize();

      await notifier.updateNotify24h(false);
      await notifier.updateNotify1h(false);
      await notifier.updateNotifyOnTime(true);

      expect(notifier.state.notify24h, false);
      expect(notifier.state.notify1h, false);
      expect(notifier.state.notifyOnTime, true);

      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getBool('water_schedule_notify_24h'), false);
      expect(prefs.getBool('water_schedule_notify_1h'), false);
      expect(prefs.getBool('water_schedule_notify_on_time'), true);
    });
  });

  group('notificationPreferencesProvider', () {
    setUpAll(() {
      TestWidgetsFlutterBinding.ensureInitialized();
    });

    setUp(() {
      SharedPreferences.setMockInitialValues({});
    });

    test('provides initial state', () async {
      final container = ProviderContainer();
      final prefs = container.read(notificationPreferencesProvider);

      expect(prefs.notify24h, true);
      expect(prefs.notify1h, true);
      expect(prefs.notifyOnTime, true);
    });

    test('allows mutations via notifier', () async {
      final container = ProviderContainer();

      await container
          .read(notificationPreferencesProvider.notifier)
          .updateNotify24h(false);

      final updated = container.read(notificationPreferencesProvider);
      expect(updated.notify24h, false);
    });

    test('persistence survives provider invalidation', () async {
      SharedPreferences.setMockInitialValues({
        'water_schedule_notify_24h': false,
      });

      final container = ProviderContainer();
      await container
          .read(notificationPreferencesProvider.notifier)
          .initialize();

      // Verify initial load
      final initial = container.read(notificationPreferencesProvider);
      expect(initial.notify24h, false);

      // Invalidate and watch again (simulating app restart scenario)
      container.invalidate(notificationPreferencesProvider);

      // New container simulates fresh provider initialization
      final container2 = ProviderContainer();
      await container2
          .read(notificationPreferencesProvider.notifier)
          .initialize();

      final reloaded = container2.read(notificationPreferencesProvider);
      expect(reloaded.notify24h, false); // persisted value restored
    });
  });
}
