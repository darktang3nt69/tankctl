import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/api/api_constants.dart';
import 'package:tankctl_app/services/device_service.dart';

/// Fetches live device info from GET /devices/{id}.
final deviceProvider = FutureProvider<Map<String, dynamic>>((ref) {
  return ref.watch(deviceServiceProvider).getDevice(ApiConstants.defaultDeviceId);
});

/// Fetches the full list of registered devices from GET /devices.
final devicesListProvider = FutureProvider<List<Map<String, dynamic>>>((ref) {
  return ref.watch(deviceServiceProvider).getDevices();
});

/// Fetches shadow (desired + reported) for a specific device.
final deviceShadowProvider =
    FutureProvider.family<Map<String, dynamic>, String>(
  (ref, deviceId) =>
      ref.watch(deviceServiceProvider).getDeviceShadow(deviceId),
);
