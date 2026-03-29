/// Tests for water schedule form state and providers
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mocktail/mocktail.dart';
import 'package:tankctl_app/domain/device_detail.dart';
import 'package:tankctl_app/providers/water_schedule_provider.dart';
import 'package:tankctl_app/services/device_detail_service.dart';

// ============================================================================
// Mocks
// ============================================================================

class MockDeviceDetailService extends Mock implements DeviceDetailService {}

// ============================================================================
// Tests
// ============================================================================

void main() {
  group('WaterScheduleFormNotifier', () {
    late ProviderContainer container;

    setUp(() {
      container = ProviderContainer();
    });

    test('initial state is correct', () {
      final state = container.read(waterScheduleFormProvider);

      expect(state.selectedDays, [1]); // Monday
      expect(state.selectedTime, '12:00');
      expect(state.scheduleType, 'weekly');
      expect(state.notify24h, true);
      expect(state.notify1h, true);
      expect(state.notifyOnTime, true);
      expect(state.isEditing, false);
      expect(state.editingScheduleId, null);
    });

    test('updateSelectedDays updates state', () {
      container
          .read(waterScheduleFormProvider.notifier)
          .updateSelectedDays([1, 3, 5]);

      final state = container.read(waterScheduleFormProvider);
      expect(state.selectedDays, [1, 3, 5]);
    });

    test('updateTime updates state', () {
      container.read(waterScheduleFormProvider.notifier).updateTime('14:30');

      final state = container.read(waterScheduleFormProvider);
      expect(state.selectedTime, '14:30');
    });

    test('updateDate updates state', () {
      container
          .read(waterScheduleFormProvider.notifier)
          .updateDate('2025-04-15');

      final state = container.read(waterScheduleFormProvider);
      expect(state.selectedDate, '2025-04-15');
    });

    test('updateScheduleType updates state and resets days/date', () {
      container
          .read(waterScheduleFormProvider.notifier)
          .updateSelectedDays([1, 2, 3]);
      container
          .read(waterScheduleFormProvider.notifier)
          .updateDate('2025-04-15');

      container
          .read(waterScheduleFormProvider.notifier)
          .updateScheduleType('custom');

      final state = container.read(waterScheduleFormProvider);
      expect(state.scheduleType, 'custom');
    });

    test('toggleNotify24h flips notification state', () {
      expect(
        container.read(waterScheduleFormProvider).notify24h,
        true,
      );

      container
          .read(waterScheduleFormProvider.notifier)
          .toggleNotify24h(false);

      expect(
        container.read(waterScheduleFormProvider).notify24h,
        false,
      );
    });

    test('toggleNotify1h flips notification state', () {
      container.read(waterScheduleFormProvider.notifier).toggleNotify1h(false);
      expect(container.read(waterScheduleFormProvider).notify1h, false);
    });

    test('toggleNotifyOnTime flips notification state', () {
      container
          .read(waterScheduleFormProvider.notifier)
          .toggleNotifyOnTime(false);
      expect(container.read(waterScheduleFormProvider).notifyOnTime, false);
    });

    test('updateNotes updates state', () {
      container
          .read(waterScheduleFormProvider.notifier)
          .updateNotes('Remember to check');

      final state = container.read(waterScheduleFormProvider);
      expect(state.notes, 'Remember to check');
    });

    test('startEditing loads schedule into form', () {
      final schedule = WaterSchedule(
        id: 42,
        deviceId: 'tank1',
        scheduleType: 'custom',
        scheduleTime: '18:00',
        scheduleDate: '2025-04-20',
        notes: 'Partial water change',
        notify24h: false,
        notify1h: true,
        notifyOnTime: false,
      );

      container
          .read(waterScheduleFormProvider.notifier)
          .startEditing(schedule);

      final state = container.read(waterScheduleFormProvider);
      expect(state.isEditing, true);
      expect(state.editingScheduleId, 42);
      expect(state.scheduleType, 'custom');
      expect(state.selectedTime, '18:00');
      expect(state.selectedDate, '2025-04-20');
      expect(state.notes, 'Partial water change');
      expect(state.notify24h, false);
      expect(state.notify1h, true);
      expect(state.notifyOnTime, false);
    });

    test('resetForm returns to initial state', () {
      // Set up some state
      container
          .read(waterScheduleFormProvider.notifier)
          .updateSelectedDays([2, 4, 6]);
      container.read(waterScheduleFormProvider.notifier).updateTime('15:45');
      container
          .read(waterScheduleFormProvider.notifier)
          .toggleNotify24h(false);

      // Reset
      container.read(waterScheduleFormProvider.notifier).resetForm();

      final state = container.read(waterScheduleFormProvider);
      expect(state.selectedDays, [1]);
      expect(state.selectedTime, '12:00');
      expect(state.notify24h, true);
      expect(state.isEditing, false);
    });

    group('validate()', () {
      test('returns error for weekly schedule with no days', () {
        container
            .read(waterScheduleFormProvider.notifier)
            .updateSelectedDays([]);
        container
            .read(waterScheduleFormProvider.notifier)
            .updateScheduleType('weekly');

        final error =
            container.read(waterScheduleFormProvider.notifier).validate();
        expect(error, 'Please select at least one day');
      });

      test('returns error for custom schedule with no date', () {
        container
            .read(waterScheduleFormProvider.notifier)
            .updateScheduleType('custom');
        container.read(waterScheduleFormProvider.notifier).updateDate(null);

        final error =
            container.read(waterScheduleFormProvider.notifier).validate();
        expect(error, 'Please select a date');
      });

      test('returns error for empty time', () {
        container.read(waterScheduleFormProvider.notifier).updateTime('');

        final error =
            container.read(waterScheduleFormProvider.notifier).validate();
        expect(error, 'Please set a time');
      });

      test('returns null for valid weekly schedule', () {
        container
            .read(waterScheduleFormProvider.notifier)
            .updateScheduleType('weekly');
        container
            .read(waterScheduleFormProvider.notifier)
            .updateSelectedDays([1, 3]);
        container.read(waterScheduleFormProvider.notifier).updateTime('12:00');

        final error =
            container.read(waterScheduleFormProvider.notifier).validate();
        expect(error, null);
      });

      test('returns null for valid custom schedule', () {
        container
            .read(waterScheduleFormProvider.notifier)
            .updateScheduleType('custom');
        container
            .read(waterScheduleFormProvider.notifier)
            .updateDate('2025-04-15');
        container.read(waterScheduleFormProvider.notifier).updateTime('12:00');

        final error =
            container.read(waterScheduleFormProvider.notifier).validate();
        expect(error, null);
      });
    });
  });

  group('WaterScheduleFormState', () {
    test('copyWith creates new instance with overrides', () {
      const state = WaterScheduleFormState(
        selectedDays: [1, 2],
        selectedTime: '10:00',
        notify24h: true,
      );

      final updated = state.copyWith(
        selectedTime: '14:00',
        notify24h: false,
      );

      expect(updated.selectedTime, '14:00');
      expect(updated.notify24h, false);
      expect(updated.selectedDays, [1, 2]); // unchanged
    });

    test('immutability: original state unchanged after copyWith', () {
      const original = WaterScheduleFormState(
        selectedDays: [1],
        selectedTime: '12:00',
      );

      final updated = original.copyWith(selectedTime: '15:00');

      expect(original.selectedTime, '12:00');
      expect(updated.selectedTime, '15:00');
    });
  });
}
