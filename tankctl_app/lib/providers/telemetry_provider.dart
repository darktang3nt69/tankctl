import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/services/telemetry_service.dart';
import 'package:tankctl_app/services/websocket_service.dart';

/// Temperature history (oldest-first, 20 readings) for a specific device.
/// Used to render sparkline charts on the dashboard.
final temperatureHistoryProvider = FutureProvider.family<List<double>, String>(
  (ref, deviceId) => ref
      .watch(telemetryServiceProvider)
      .getTemperatureHistory(deviceId, limit: 20),
);

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
