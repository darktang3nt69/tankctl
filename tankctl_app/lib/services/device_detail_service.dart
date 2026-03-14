/// Device detail service for API calls
library;

import 'package:dio/dio.dart';
import 'package:tankctl_app/domain/device_detail.dart';

/// Service for device detail operations
class DeviceDetailService {
  final Dio dio;

  DeviceDetailService(this.dio);

  /// Get complete device detail with all settings
  Future<DeviceDetail> getDeviceDetail(String deviceId) async {
    try {
      final response = await dio.get('/devices/$deviceId/detail');

      if (response.statusCode == 200) {
        return DeviceDetail.fromJson(response.data);
      }
      throw Exception('Failed to fetch device detail: ${response.statusCode}');
    } on DioException catch (e) {
      throw Exception('API error: ${e.message}');
    }
  }

  /// Update device metadata (name, location, icon, thresholds)
  Future<void> updateDeviceMetadata(
    String deviceId, {
    String? deviceName,
    String? location,
    String? iconType,
    String? description,
    double? tempThresholdLow,
    double? tempThresholdHigh,
  }) async {
    try {
      final data = <String, dynamic>{};
      if (deviceName != null) data['device_name'] = deviceName;
      if (location != null) data['location'] = location;
      if (iconType != null) data['icon_type'] = iconType;
      if (description != null) data['description'] = description;
      if (tempThresholdLow != null) data['temp_threshold_low'] = tempThresholdLow;
      if (tempThresholdHigh != null) data['temp_threshold_high'] = tempThresholdHigh;

      await dio.put('/devices/$deviceId', data: data);
    } on DioException catch (e) {
      throw Exception('Failed to update device: ${e.message}');
    }
  }

  /// Set or update light schedule
  Future<LightSchedule> setLightSchedule(
    String deviceId, {
    required String startTime,
    required String endTime,
    required bool enabled,
  }) async {
    try {
      final response = await dio.post(
        '/devices/$deviceId/schedule',
        data: {
          'start_time': startTime,
          'end_time': endTime,
          'enabled': enabled,
        },
      );

      return LightSchedule.fromJson(response.data);
    } on DioException catch (e) {
      throw Exception('Failed to set light schedule: ${e.message}');
    }
  }

  /// Get light schedule
  Future<LightSchedule?> getLightSchedule(String deviceId) async {
    try {
      final response = await dio.get('/devices/$deviceId/schedule');

      return LightSchedule.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        return null;
      }
      throw Exception('Failed to get light schedule: ${e.message}');
    }
  }

  /// Create water change schedule
  Future<WaterSchedule> createWaterSchedule(
    String deviceId, {
    required String scheduleType,
    int? dayOfWeek,
    String? scheduleDate,
    required String scheduleTime,
    String? notes,
  }) async {
    try {
      final data = <String, dynamic>{
        'schedule_type': scheduleType,
        'schedule_time': scheduleTime,
      };
      if (dayOfWeek != null) data['day_of_week'] = dayOfWeek;
      if (scheduleDate != null) data['schedule_date'] = scheduleDate;
      if (notes != null) data['notes'] = notes;

      final response = await dio.post(
        '/devices/$deviceId/water-schedules',
        data: data,
      );

      return WaterSchedule.fromJson(response.data);
    } on DioException catch (e) {
      throw Exception('Failed to create water schedule: ${e.message}');
    }
  }

  /// Get all water schedules for device
  Future<List<WaterSchedule>> getWaterSchedules(String deviceId) async {
    try {
      final response = await dio.get('/devices/$deviceId/water-schedules');

      final List<dynamic> data = response.data;
      return data.map((json) => WaterSchedule.fromJson(json as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw Exception('Failed to get water schedules: ${e.message}');
    }
  }

  /// Delete water schedule
  Future<void> deleteWaterSchedule(String deviceId, int scheduleId) async {
    try {
      await dio.delete(
        '/devices/$deviceId/water-schedules/$scheduleId',
      );
    } on DioException catch (e) {
      throw Exception('Failed to delete water schedule: ${e.message}');
    }
  }
}
