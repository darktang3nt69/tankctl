import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/api/api_client.dart';

class DeviceService {
  DeviceService(this._dio);
  final Dio _dio;

  Future<Map<String, dynamic>> getDevice(String deviceId) async {
    final response = await _dio.get('/devices/$deviceId');
    return response.data as Map<String, dynamic>;
  }

  Future<List<Map<String, dynamic>>> getDevices() async {
    final response = await _dio.get('/devices');
    final data = response.data as Map<String, dynamic>;
    return (data['devices'] as List).cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> getDeviceShadow(String deviceId) async {
    final response = await _dio.get('/devices/$deviceId/shadow');
    return response.data as Map<String, dynamic>;
  }

  Future<void> requestStatus(String deviceId) async {
    await _dio.post('/devices/$deviceId/request-status');
  }

  Future<void> rebootDevice(String deviceId) async {
    await _dio.post('/devices/$deviceId/reboot');
  }

  Future<void> acknowledgeWarning(String deviceId, String warningCode) async {
    await _dio.post('/devices/$deviceId/warnings/$warningCode/ack');
  }

  Future<Set<String>> getAcknowledgedIssueKeys() async {
    final response = await _dio.get('/devices/warnings/acks');
    final data = response.data;
    if (data is! List) {
      return <String>{};
    }

    final keys = <String>{};
    for (final row in data) {
      if (row is! Map) {
        continue;
      }
      final deviceId = row['device_id'];
      final warningCode = row['warning_code'];
      if (deviceId is String && warningCode is String && warningCode.isNotEmpty) {
        keys.add('${deviceId}_$warningCode');
      }
    }
    return keys;
  }
}

final deviceServiceProvider = Provider<DeviceService>(
  (ref) => DeviceService(ref.watch(dioProvider)),
);
