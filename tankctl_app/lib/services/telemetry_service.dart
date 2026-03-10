import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/api/api_client.dart';

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
    return (readings.first['value'] as num?)?.toDouble();
  }

  /// Returns the recorded_at timestamp of the most recent telemetry entry.
  Future<DateTime?> getLatestReadingTime(String deviceId) async {
    final response = await _dio.get(
      '/devices/$deviceId/telemetry/temperature',
      queryParameters: {'limit': 1},
    );
    final data = response.data as Map<String, dynamic>;
    final readings = data['data'] as List?;
    if (readings == null || readings.isEmpty) return null;
    final raw = readings.first['time'] as String?;
    if (raw == null) return null;
    // Ensure the string is treated as UTC before converting to local.
    final utcString = raw.endsWith('Z') || raw.contains('+') ? raw : '${raw}Z';
    return DateTime.tryParse(utcString)?.toLocal();
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
        .map((r) => (r['value'] as num?)?.toDouble() ?? 0.0)
        .toList()
        .reversed
        .toList();
  }
}

final telemetryServiceProvider = Provider<TelemetryService>(
  (ref) => TelemetryService(ref.watch(dioProvider)),
);
