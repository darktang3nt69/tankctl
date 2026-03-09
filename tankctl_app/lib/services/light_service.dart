import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/api/api_client.dart';

class LightService {
  LightService(this._dio);
  final Dio _dio;

  /// Gets the current light state from the device shadow's reported field.
  Future<bool> getLightState(String deviceId) async {
    final response = await _dio.get('/devices/$deviceId/shadow');
    final reported =
        (response.data as Map<String, dynamic>)['reported'] as Map<String, dynamic>?;
    return reported?['light'] == 'on';
  }

  /// Sends a set_light command via POST /devices/{id}/light.
  Future<void> setLight(String deviceId, bool on) async {
    await _dio.post(
      '/devices/$deviceId/light',
      data: {'state': on ? 'on' : 'off'},
    );
  }
}

final lightServiceProvider = Provider<LightService>(
  (ref) => LightService(ref.watch(dioProvider)),
);
