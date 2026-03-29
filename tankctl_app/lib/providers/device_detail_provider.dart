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






