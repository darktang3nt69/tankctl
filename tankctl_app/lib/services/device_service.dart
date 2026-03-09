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
}

final deviceServiceProvider = Provider<DeviceService>(
  (ref) => DeviceService(ref.watch(dioProvider)),
);
