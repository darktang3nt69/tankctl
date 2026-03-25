/// Device detail domain model
library;

/// Complete device detail with all settings
class DeviceDetail {
  final String deviceId;
  final String? deviceName;
  final String? location;
  final String iconType;
  final String? description;
  final String status;
  final String? firmwareVersion;
  final String? createdAt;
  final String? lastSeen;
  final int? uptimeMs;
  final int? rssi;
  final String? wifiStatus;
  final double? tempThresholdLow;
  final double? tempThresholdHigh;
  final LightSchedule? lightSchedule;
  final List<WaterSchedule> waterSchedules;

  const DeviceDetail({
    required this.deviceId,
    this.deviceName,
    this.location,
    this.iconType = 'fish_bowl',
    this.description,
    required this.status,
    this.firmwareVersion,
    this.createdAt,
    this.lastSeen,
    this.uptimeMs,
    this.rssi,
    this.wifiStatus,
    this.tempThresholdLow,
    this.tempThresholdHigh,
    this.lightSchedule,
    this.waterSchedules = const [],
  });

  factory DeviceDetail.fromJson(Map<String, dynamic> json) {
    return DeviceDetail(
      deviceId: json['device_id'] ?? json['deviceId'] ?? '',
      deviceName: json['device_name'] ?? json['deviceName'],
      location: json['location'],
      iconType: json['icon_type'] ?? json['iconType'] ?? 'fish_bowl',
      description: json['description'],
      status: json['status'] ?? 'offline',
      firmwareVersion: json['firmware_version'] ?? json['firmwareVersion'],
      createdAt: json['created_at'] ?? json['createdAt'],
      lastSeen: json['last_seen'] ?? json['lastSeen'],
      uptimeMs: json['uptime_ms'] ?? json['uptimeMs'],
      rssi: json['rssi'],
      wifiStatus: json['wifi_status'] ?? json['wifiStatus'],
      tempThresholdLow: (json['temp_threshold_low'] ?? json['tempThresholdLow'])?.toDouble(),
      tempThresholdHigh: (json['temp_threshold_high'] ?? json['tempThresholdHigh'])?.toDouble(),
      lightSchedule: json['light_schedule'] != null
          ? LightSchedule.fromJson(json['light_schedule'])
          : null,
      waterSchedules: (json['water_schedules'] as List<dynamic>?)
          ?.map((e) => WaterSchedule.fromJson(e))
          .toList() ?? [],
    );
  }

  Map<String, dynamic> toJson() => {
    'device_id': deviceId,
    'device_name': deviceName,
    'location': location,
    'icon_type': iconType,
    'description': description,
    'status': status,
    'firmware_version': firmwareVersion,
    'created_at': createdAt,
    'last_seen': lastSeen,
    'uptime_ms': uptimeMs,
    'rssi': rssi,
    'wifi_status': wifiStatus,
    'temp_threshold_low': tempThresholdLow,
    'temp_threshold_high': tempThresholdHigh,
    'light_schedule': lightSchedule?.toJson(),
    'water_schedules': waterSchedules.map((e) => e.toJson()).toList(),
  };
}

/// Light schedule settings
class LightSchedule {
  final int id;
  final String deviceId;
  final bool enabled;
  final String startTime;
  final String endTime;
  final String? createdAt;
  final String? updatedAt;

  const LightSchedule({
    required this.id,
    required this.deviceId,
    this.enabled = true,
    required this.startTime,
    required this.endTime,
    this.createdAt,
    this.updatedAt,
  });

  factory LightSchedule.fromJson(Map<String, dynamic> json) {
    return LightSchedule(
      id: json['id'] ?? 0,
      deviceId: json['device_id'] ?? json['deviceId'] ?? '',
      enabled: json['enabled'] ?? true,
      startTime: json['on_time'] ?? json['start_time'] ?? json['startTime'] ?? '08:00',
      endTime: json['off_time'] ?? json['end_time'] ?? json['endTime'] ?? '20:00',
      createdAt: json['created_at'] ?? json['createdAt'],
      updatedAt: json['updated_at'] ?? json['updatedAt'],
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'device_id': deviceId,
    'enabled': enabled,
    'start_time': startTime,
    'end_time': endTime,
    'created_at': createdAt,
    'updated_at': updatedAt,
  };
}

/// Water schedule reminder
class WaterSchedule {
  final int id;
  final String deviceId;
  final String scheduleType;
  final List<int> daysOfWeek;  // For weekly: [1,3,5] = Mon,Wed,Fri
  final String? scheduleDate;
  final String scheduleTime;
  final String? notes;
  final bool completed;
  final bool enabled;
  final String? createdAt;
  final String? updatedAt;

  const WaterSchedule({
    required this.id,
    required this.deviceId,
    required this.scheduleType,
    this.daysOfWeek = const [],
    this.scheduleDate,
    required this.scheduleTime,
    this.notes,
    this.completed = false,
    this.enabled = true,
    this.createdAt,
    this.updatedAt,
  });

  factory WaterSchedule.fromJson(Map<String, dynamic> json) {
    // Parse days_of_week from comma-separated string or list
    List<int> daysOfWeek = [];
    final doWValue = json['days_of_week'] ?? json['daysOfWeek'];
    if (doWValue != null) {
      if (doWValue is String && doWValue.isNotEmpty) {
        daysOfWeek = doWValue.split(',').map((d) => int.parse(d.trim())).toList();
      } else if (doWValue is List) {
        daysOfWeek = List<int>.from(doWValue);
      }
    }
    
    return WaterSchedule(
      id: json['id'] ?? 0,
      deviceId: json['device_id'] ?? json['deviceId'] ?? '',
      scheduleType: json['schedule_type'] ?? json['scheduleType'] ?? 'weekly',
      daysOfWeek: daysOfWeek,
      scheduleDate: json['schedule_date'] ?? json['scheduleDate'],
      scheduleTime: json['schedule_time'] ?? json['scheduleTime'] ?? '12:00',
      notes: json['notes'],
      completed: json['completed'] ?? false,
      enabled: json['enabled'] ?? true,
      createdAt: json['created_at'] ?? json['createdAt'],
      updatedAt: json['updated_at'] ?? json['updatedAt'],
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'device_id': deviceId,
    'schedule_type': scheduleType,
    'days_of_week': daysOfWeek.isNotEmpty ? daysOfWeek.join(',') : null,
    'schedule_date': scheduleDate,
    'schedule_time': scheduleTime,
    'notes': notes,
    'completed': completed,
    'enabled': enabled,
    'created_at': createdAt,
    'updated_at': updatedAt,
  };

  /// Get human-readable schedule type
  String get displayType => scheduleType == 'weekly' ? 'Weekly' : 'Custom';

  /// Get human-readable day names for weekly schedules
  String? get dayNames {
    if (scheduleType != 'weekly' || daysOfWeek.isEmpty) return null;
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    return daysOfWeek.map((d) => days[d]).join(', ');
  }

  /// Get next scheduled date
  DateTime? get nextScheduledDate {
    if (scheduleType == 'custom' && scheduleDate != null) {
      return DateTime.tryParse(scheduleDate!);
    }
    return null;
  }
}
