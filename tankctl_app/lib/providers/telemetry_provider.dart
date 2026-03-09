import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/api/api_constants.dart';
import 'package:tankctl_app/services/telemetry_service.dart';

/// Latest temperature reading for the default device.
final temperatureProvider = FutureProvider<double?>((ref) {
  return ref
      .watch(telemetryServiceProvider)
      .getLatestTemperature(ApiConstants.defaultDeviceId);
});

/// Temperature history (oldest-first, 20 readings) for a specific device.
/// Used to render sparkline charts on the dashboard.
final temperatureHistoryProvider =
    FutureProvider.family<List<double>, String>(
  (ref, deviceId) => ref
      .watch(telemetryServiceProvider)
      .getTemperatureHistory(deviceId, limit: 20),
);
