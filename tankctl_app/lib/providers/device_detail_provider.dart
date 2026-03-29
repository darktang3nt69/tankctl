/// Device detail providers for Riverpod state management
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/api/api_client.dart';
import 'package:tankctl_app/domain/device_detail.dart';
import 'package:tankctl_app/services/device_detail_service.dart';

/// Device detail service provider
final deviceDetailServiceProvider = Provider<DeviceDetailService>((ref) {
  final dio = ref.watch(dioProvider);
  return DeviceDetailService(dio);
});

/// Get device detail (full settings, schedules, health metrics)
final deviceDetailProvider = FutureProvider.family<DeviceDetail, String>((ref, deviceId) async {
  final service = ref.watch(deviceDetailServiceProvider);
  return service.getDeviceDetail(deviceId);
});

/// Light schedule for a device
final lightScheduleProvider =
    FutureProvider.family<LightSchedule?, String>((ref, deviceId) async {
  final service = ref.watch(deviceDetailServiceProvider);
  return service.getLightSchedule(deviceId);
});

/// Water schedules for a device
final waterSchedulesProvider =
    FutureProvider.family<List<WaterSchedule>, String>((ref, deviceId) async {
  final service = ref.watch(deviceDetailServiceProvider);
  return service.getWaterSchedules(deviceId);
});

/// Light schedule enabled state for a device (for immediate UI feedback)
/// Tracks the enabled state with optimistic updates
final lightScheduleEnabledProvider =
    StateProvider.family<bool?, String>((ref, deviceId) {
  // Initialize from the device detail when it loads
  final deviceAsync = ref.watch(deviceDetailProvider(deviceId));
  return deviceAsync.whenData((device) => device.lightSchedule?.enabled).value;
});

/// Device metadata editor state (local form state)
class DeviceMetadataState {
  final String? deviceName;
  final String? location;
  final String? iconType;
  final String? description;
  final double? tempThresholdLow;
  final double? tempThresholdHigh;

  const DeviceMetadataState({
    this.deviceName,
    this.location,
    this.iconType,
    this.description,
    this.tempThresholdLow,
    this.tempThresholdHigh,
  });

  DeviceMetadataState copyWith({
    String? deviceName,
    String? location,
    String? iconType,
    String? description,
    double? tempThresholdLow,
    double? tempThresholdHigh,
  }) {
    return DeviceMetadataState(
      deviceName: deviceName ?? this.deviceName,
      location: location ?? this.location,
      iconType: iconType ?? this.iconType,
      description: description ?? this.description,
      tempThresholdLow: tempThresholdLow ?? this.tempThresholdLow,
      tempThresholdHigh: tempThresholdHigh ?? this.tempThresholdHigh,
    );
  }
}

/// Local state for device metadata form (not persisted)
final deviceMetadataEditorProvider =
    StateNotifierProvider.family<DeviceMetadataEditor, DeviceMetadataState, String>(
        (ref, deviceId) {
  return DeviceMetadataEditor(const DeviceMetadataState());
});

class DeviceMetadataEditor extends StateNotifier<DeviceMetadataState> {
  DeviceMetadataEditor(super.initialState);

  void setDeviceName(String? value) => state = state.copyWith(deviceName: value);
  void setLocation(String? value) => state = state.copyWith(location: value);
  void setIconType(String? value) => state = state.copyWith(iconType: value);
  void setDescription(String? value) => state = state.copyWith(description: value);
  void setTempThresholds(double? low, double? high) =>
      state = state.copyWith(tempThresholdLow: low, tempThresholdHigh: high);
}

/// Local state for light schedule form
class LightScheduleEditorState {
  final String startTime;
  final String endTime;
  final bool enabled;

  LightScheduleEditorState({
    this.startTime = '08:00',
    this.endTime = '20:00',
    this.enabled = true,
  });

  LightScheduleEditorState copyWith({
    String? startTime,
    String? endTime,
    bool? enabled,
  }) {
    return LightScheduleEditorState(
      startTime: startTime ?? this.startTime,
      endTime: endTime ?? this.endTime,
      enabled: enabled ?? this.enabled,
    );
  }
}

/// Light schedule editor provider
final lightScheduleEditorProvider = StateNotifierProvider<LightScheduleEditor, LightScheduleEditorState>((ref) {
  return LightScheduleEditor(LightScheduleEditorState());
});

class LightScheduleEditor extends StateNotifier<LightScheduleEditorState> {
  LightScheduleEditor(super.initialState);

  void setStartTime(String value) => state = state.copyWith(startTime: value);
  void setEndTime(String value) => state = state.copyWith(endTime: value);
  void setEnabled(bool value) => state = state.copyWith(enabled: value);
}

/// Local state for water schedule form
class WaterScheduleEditorState {
  final String scheduleType; // 'weekly' or 'custom'
  final int? dayOfWeek; // 0-6
  final String? scheduleDate; // YYYY-MM-DD
  final String scheduleTime; // HH:MM
  final String? notes;

  WaterScheduleEditorState({
    this.scheduleType = 'weekly',
    this.dayOfWeek,
    this.scheduleDate,
    this.scheduleTime = '12:00',
    this.notes,
  });

  WaterScheduleEditorState copyWith({
    String? scheduleType,
    int? dayOfWeek,
    String? scheduleDate,
    String? scheduleTime,
    String? notes,
  }) {
    return WaterScheduleEditorState(
      scheduleType: scheduleType ?? this.scheduleType,
      dayOfWeek: dayOfWeek ?? this.dayOfWeek,
      scheduleDate: scheduleDate ?? this.scheduleDate,
      scheduleTime: scheduleTime ?? this.scheduleTime,
      notes: notes ?? this.notes,
    );
  }
}

/// Water schedule editor provider
final waterScheduleEditorProvider = StateNotifierProvider<WaterScheduleEditor, WaterScheduleEditorState>((ref) {
  return WaterScheduleEditor(WaterScheduleEditorState());
});

class WaterScheduleEditor extends StateNotifier<WaterScheduleEditorState> {
  WaterScheduleEditor(super.initialState);

  void setScheduleType(String type) => state = state.copyWith(scheduleType: type);
  void setDayOfWeek(int? day) => state = state.copyWith(dayOfWeek: day);
  void setScheduleDate(String? date) => state = state.copyWith(scheduleDate: date);
  void setScheduleTime(String time) => state = state.copyWith(scheduleTime: time);
  void setNotes(String? notes) => state = state.copyWith(notes: notes);
}
