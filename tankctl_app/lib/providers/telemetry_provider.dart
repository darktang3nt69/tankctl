import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/domain/time_range.dart';
import 'package:tankctl_app/services/telemetry_service.dart';
import 'package:tankctl_app/services/websocket_service.dart';

/// Selected time range for temperature chart visualization per device.
final temperatureTimeRangeProvider = StateProvider.family<TimeRange, String>((
  ref,
  deviceId,
) {
  return TimeRange.defaultRange;
});

/// Temperature history (oldest-first, 20 readings) for a specific device.
/// Used to render sparkline charts on the dashboard.
final temperatureHistoryProvider = FutureProvider.family<List<double>, String>(
  (ref, deviceId) => ref
      .watch(telemetryServiceProvider)
      .getTemperatureHistory(deviceId, limit: 20),
);

/// Temperature history with timestamps for the device detail chart with axes.
/// Responds to changes in the selected time range (see [temperatureTimeRangeProvider]).
final temperatureHistoryWithTimeProvider =
    FutureProvider.family<List<TelemetryReading>, String>((ref, deviceId) {
      final timeRange = ref.watch(temperatureTimeRangeProvider(deviceId));
      return ref
          .watch(telemetryServiceProvider)
          .getTemperatureHistoryWithTime(deviceId, limit: timeRange.apiLimit);
    });

/// Live temperature stream for a device, driven by WebSocket telemetry events.
/// Iterates directly over the persistent broadcast stream from [WebSocketService]
/// so new readings arrive as long as the WebSocket stays connected.
final liveTelemetryProvider = StreamProvider.family<double?, String>((
  ref,
  deviceId,
) async* {
  final service = ref.watch(webSocketServiceProvider);
  await for (final event in service.stream) {
    if (event['event'] == 'telemetry_received' &&
        event['device_id'] == deviceId) {
      final metrics = event['metadata'] as Map<String, dynamic>?;
      yield normalizeTemperatureReading(metrics?['temperature']);
    }
  }
});

/// Wall-clock time of the last telemetry received for a device.
/// Updated live by the WebSocket handler.
final lastTelemetryTimeProvider = StateProvider.family<DateTime?, String>(
  (ref, deviceId) => null,
);

/// Ticks every second — watched by TankCard to keep "Xs ago" labels current.
final secondTickProvider = StreamProvider<int>((ref) {
  return Stream.periodic(const Duration(seconds: 1), (i) => i);
});

/// Latest warning code received from the backend for a device.
/// Set when a `device_warning` WS event arrives; cleared when a valid
/// temperature reading arrives (sensor reconnected).
final deviceWarningProvider = StateProvider.family<String?, String>(
  (ref, deviceId) => null,
);
