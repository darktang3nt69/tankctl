/// Water schedule Riverpod providers for form state and API operations
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/domain/device_detail.dart';
import 'package:tankctl_app/services/device_detail_service.dart';
import 'package:tankctl_app/providers/device_detail_provider.dart';

// ============================================================================
// State Models
// ============================================================================

/// Form state for water schedule creation and editing
class WaterScheduleFormState {
  final List<int> selectedDays;
  final String? selectedDate;
  final String selectedTime;
  final String scheduleType;
  final bool notify24h;
  final bool notify1h;
  final bool notifyOnTime;
  final String? notes;
  final bool isEditing;
  final int? editingScheduleId;

  const WaterScheduleFormState({
    this.selectedDays = const [1], // Default: Monday
    this.selectedDate,
    this.selectedTime = '12:00',
    this.scheduleType = 'weekly',
    this.notify24h = true,
    this.notify1h = true,
    this.notifyOnTime = true,
    this.notes,
    this.isEditing = false,
    this.editingScheduleId,
  });

  /// Create a copy with optional overrides
  WaterScheduleFormState copyWith({
    List<int>? selectedDays,
    String? selectedDate,
    String? selectedTime,
    String? scheduleType,
    bool? notify24h,
    bool? notify1h,
    bool? notifyOnTime,
    String? notes,
    bool? isEditing,
    int? editingScheduleId,
  }) {
    return WaterScheduleFormState(
      selectedDays: selectedDays ?? this.selectedDays,
      selectedDate: selectedDate ?? this.selectedDate,
      selectedTime: selectedTime ?? this.selectedTime,
      scheduleType: scheduleType ?? this.scheduleType,
      notify24h: notify24h ?? this.notify24h,
      notify1h: notify1h ?? this.notify1h,
      notifyOnTime: notifyOnTime ?? this.notifyOnTime,
      notes: notes ?? this.notes,
      isEditing: isEditing ?? this.isEditing,
      editingScheduleId: editingScheduleId ?? this.editingScheduleId,
    );
  }
}

// ============================================================================
// Form State Notifier
// ============================================================================

/// State notifier for managing water schedule form state
class WaterScheduleFormNotifier extends StateNotifier<WaterScheduleFormState> {
  WaterScheduleFormNotifier()
      : super(const WaterScheduleFormState());

  /// Update selected days of week
  void updateSelectedDays(List<int> days) {
    state = state.copyWith(selectedDays: days);
  }

  /// Update selected time
  void updateTime(String time) {
    state = state.copyWith(selectedTime: time);
  }

  /// Update selected date
  void updateDate(String? date) {
    state = state.copyWith(selectedDate: date);
  }

  /// Update schedule type (weekly/custom)
  void updateScheduleType(String type) {
    state = state.copyWith(scheduleType: type);
  }

  /// Toggle 24h notification
  void toggleNotify24h(bool value) {
    state = state.copyWith(notify24h: value);
  }

  /// Toggle 1h notification
  void toggleNotify1h(bool value) {
    state = state.copyWith(notify1h: value);
  }

  /// Toggle on-time notification
  void toggleNotifyOnTime(bool value) {
    state = state.copyWith(notifyOnTime: value);
  }

  /// Update notes
  void updateNotes(String? notes) {
    state = state.copyWith(notes: notes);
  }

  /// Start editing a schedule
  void startEditing(WaterSchedule schedule) {
    state = WaterScheduleFormState(
      selectedDays: List.from(schedule.daysOfWeek),
      selectedDate: schedule.scheduleDate,
      selectedTime: schedule.scheduleTime,
      scheduleType: schedule.scheduleType,
      notify24h: schedule.notify24h,
      notify1h: schedule.notify1h,
      notifyOnTime: schedule.notifyOnTime,
      notes: schedule.notes,
      isEditing: true,
      editingScheduleId: schedule.id,
    );
  }

  /// Reset form to initial state
  void resetForm() {
    state = const WaterScheduleFormState();
  }

  /// Validate the form state
  /// Returns error message if invalid, null if valid
  String? validate() {
    if (state.scheduleType == 'weekly' && state.selectedDays.isEmpty) {
      return 'Please select at least one day';
    }
    if (state.scheduleType == 'custom' && state.selectedDate == null) {
      return 'Please select a date';
    }
    if (state.selectedTime.isEmpty) {
      return 'Please set a time';
    }
    return null;
  }
}

// ============================================================================
// Providers
// ============================================================================

/// Form state provider
final waterScheduleFormProvider =
    StateNotifierProvider<WaterScheduleFormNotifier, WaterScheduleFormState>(
  (ref) => WaterScheduleFormNotifier(),
);

/// Create water schedule provider
/// Returns the created schedule on success
final createWaterScheduleProvider =
    FutureProvider.family<WaterSchedule, String>((ref, deviceId) async {
  final service = ref.watch(deviceDetailServiceProvider);
  final formState = ref.watch(waterScheduleFormProvider);

  return service.createWaterSchedule(
    deviceId,
    scheduleType: formState.scheduleType,
    daysOfWeek: formState.scheduleType == 'weekly' ? formState.selectedDays : null,
    scheduleDate: formState.scheduleType == 'custom' ? formState.selectedDate : null,
    scheduleTime: formState.selectedTime,
    notes: formState.notes,
    enabled: true,
    notify24h: formState.notify24h,
    notify1h: formState.notify1h,
    notifyOnTime: formState.notifyOnTime,
  );
});

/// Update water schedule provider
/// Returns the updated schedule on success
final updateWaterScheduleProvider =
    FutureProvider.family<WaterSchedule, String>((ref, deviceId) async {
  final service = ref.watch(deviceDetailServiceProvider);
  final formState = ref.watch(waterScheduleFormProvider);

  if (!formState.isEditing || formState.editingScheduleId == null) {
    throw Exception('Not in editing mode');
  }

  return service.updateWaterSchedule(
    deviceId,
    formState.editingScheduleId!,
    scheduleType: formState.scheduleType,
    daysOfWeek: formState.scheduleType == 'weekly' ? formState.selectedDays : null,
    scheduleDate: formState.scheduleType == 'custom' ? formState.selectedDate : null,
    scheduleTime: formState.selectedTime,
    notes: formState.notes,
    notify24h: formState.notify24h,
    notify1h: formState.notify1h,
    notifyOnTime: formState.notifyOnTime,
  );
});

/// Delete water schedule provider
final deleteWaterScheduleProvider =
    FutureProvider.family<void, ({String deviceId, int scheduleId})>(
      (ref, params) async {
    final service = ref.watch(deviceDetailServiceProvider);
    await service.deleteWaterSchedule(params.deviceId, params.scheduleId);
  },
);
