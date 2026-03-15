import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/api/api_client.dart';

double? normalizeTemperatureReading(Object? raw) {
  final value = (raw as num?)?.toDouble();
  if (value == null || value == 0) {
    return null;
  }
  return value;
}

class TelemetryService {
  TelemetryService(this._dio);
  final Dio _dio;

  Future<double?> getLatestTemperature(String deviceId) async {
    final response = await _dio.get(
      '/devices/$deviceId/telemetry/temperature',
      queryParameters: {'limit': 1},
    );
    final data = response.data as Map<String, dynamic>;
    final readings = data['data'] as List?;
    if (readings == null || readings.isEmpty) return null;
    return normalizeTemperatureReading(
      (readings.first as Map<String, dynamic>)['value'],
    );
  }

  /// Returns temperature readings oldest-first for sparkline charts.
  Future<List<double>> getTemperatureHistory(
    String deviceId, {
    int limit = 20,
  }) async {
    final response = await _dio.get(
      '/devices/$deviceId/telemetry/temperature',
      queryParameters: {'limit': limit},
    );
    final data = response.data as Map<String, dynamic>;
    final readings = (data['data'] as List?) ?? [];
    return readings
        .map(
          (r) =>
              normalizeTemperatureReading((r as Map<String, dynamic>)['value']),
        )
        .whereType<double>()
        .toList()
        .reversed
        .toList();
  }

  /// Returns temperature readings with timestamps, oldest-first.
  /// Used for the detail chart with axes.
  Future<List<TelemetryReading>> getTemperatureHistoryWithTime(
    String deviceId, {
    int limit = 50,
  }) async {
    final response = await _dio.get(
      '/devices/$deviceId/telemetry/temperature',
      queryParameters: {'limit': limit},
    );
    final data = response.data as Map<String, dynamic>;
    final readings = (data['data'] as List?) ?? [];
    final result = <TelemetryReading>[];
    for (final r in readings) {
      final map = r as Map<String, dynamic>;
      final value = normalizeTemperatureReading(map['value']);
      if (value == null) continue;
      final timeStr = map['time'] as String?;
      final time = timeStr != null ? DateTime.tryParse(timeStr) : null;
      result.add(TelemetryReading(value: value, time: time?.toLocal()));
    }
    // API returns newest-first; reverse to oldest-first.
    return result.reversed.toList();
  }
}

/// A single telemetry reading with an optional timestamp.
class TelemetryReading {
  const TelemetryReading({required this.value, this.time});
  final double value;
  final DateTime? time;
}

final telemetryServiceProvider = Provider<TelemetryService>(
  (ref) => TelemetryService(ref.watch(dioProvider)),
);
