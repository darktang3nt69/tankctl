/// Event API service for TankCtl
/// Handles all event-related backend communication
library;

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:tankctl_app/domain/event.dart';

class EventService {
  final Dio _dio;

  EventService(this._dio);

  /// Fetch paginated events from backend
  /// Parameters allow filtering by tank, category, severity, and date range
  Future<Map<String, dynamic>> getEvents({
    required int limit,
    int offset = 0,
    String? tankId,
    EventCategory? category,
    EventSeverity? severity,
    DateTime? fromDate,
    DateTime? toDate,
    String sortOrder = 'newest',
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'limit': limit,
        'offset': offset,
      };

      if (tankId != null) queryParams['tankId'] = tankId;
      if (category != null) queryParams['category'] = category.name;
      if (severity != null) queryParams['severity'] = severity.name;
      if (fromDate != null) queryParams['from'] = fromDate.toIso8601String();
      if (toDate != null) queryParams['to'] = toDate.toIso8601String();
      if (sortOrder != 'newest') queryParams['sort'] = sortOrder;

      final response = await _dio.get(
        '/events',
        queryParameters: queryParams,
      );

      // Handle both wrapped (Map) and direct (List) API responses
      List<dynamic> rawEventsList;
      Map<String, dynamic>? metadata;

      if (response.data is List<dynamic>) {
        // API returns list directly
        rawEventsList = response.data as List<dynamic>;
        metadata = null;
      } else if (response.data is Map<String, dynamic>) {
        // API returns wrapped response with metadata
        final data = response.data as Map<String, dynamic>;
        rawEventsList = (data['events'] as List<dynamic>? ?? []);
        metadata = data;
      } else {
        throw EventServiceException('Unexpected API response type: ${response.data.runtimeType}');
      }

      final eventsList = rawEventsList
          .map((e) {
            try {
              return _mapApiResponseToEvent(e as Map<String, dynamic>);
            } catch (e) {
              debugPrint('Failed to parse event: $e');
              return null;
            }
          })
          .whereType<Event>()
          .toList();

      return {
        'events': eventsList,
        'total': metadata?['total'] as int? ?? eventsList.length,
        'offset': metadata?['offset'] as int? ?? offset,
        'limit': metadata?['limit'] as int? ?? limit,
      };
    } catch (e) {
      throw EventServiceException('Failed to fetch events: $e');
    }
  }

  /// Fetch a single event by ID
  Future<Event> getEventById(String id) async {
    try {
      final response = await _dio.get('/events/$id');
      return Event.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw EventServiceException('Failed to fetch event $id: $e');
    }
  }

  /// Map backend API response to Event domain model
  Event _mapApiResponseToEvent(Map<String, dynamic> raw) {
    final eventType = raw['event'] as String? ?? 'unknown';
    final deviceId = raw['device_id'] as String? ?? 'unknown';
    final timestamp = _parseTimestamp(raw['timestamp']);
    final metadata = (raw['metadata'] as Map<String, dynamic>?) ?? {};

    // Parse event category and severity from event type
    final (category, severity, title, description) = _parseEventType(eventType, metadata);

    // Extract sensor values from metadata if available
    final temperature = metadata['temperature'];
    final humidity = metadata['humidity'];
    final pressure = metadata['pressure'];

    return Event(
      id: '${deviceId}_${timestamp.millisecondsSinceEpoch}',
      tankId: _extractTankIdFromDeviceId(deviceId),
      tankName: _extractTankNameFromDeviceId(deviceId),
      deviceId: deviceId,
      deviceName: deviceId, // Use device_id as device name
      category: category,
      type: eventType,
      title: title,
      description: description,
      severity: severity,
      timestamp: timestamp,
      value: temperature ?? humidity ?? pressure,
      threshold: null,
      source: 'device',
      isAcknowledged: false,
      isRead: false,
    );
  }

  /// Parse event type to determine category, severity, title, and description
  (EventCategory, EventSeverity, String, String) _parseEventType(
    String eventType,
    Map<String, dynamic> metadata,
  ) {
    switch (eventType) {
      case 'telemetry_received':
        return (
          EventCategory.temperature,
          EventSeverity.info,
          'Telemetry Update',
          'Device sent sensor readings',
        );
      case 'device_warning':
        final warningCode = metadata['code'] as String? ?? 'Unknown';
        final warningMsg = metadata['message'] as String? ?? 'Device reported a warning';
        return (
          EventCategory.system,
          EventSeverity.warning,
          'Device Warning: $warningCode',
          warningMsg,
        );
      case 'device_error':
        final errorCode = metadata['code'] as String? ?? 'Unknown';
        final errorMsg = metadata['message'] as String? ?? 'Device reported an error';
        return (
          EventCategory.system,
          EventSeverity.critical,
          'Device Error: $errorCode',
          errorMsg,
        );
      case 'connectivity_lost':
        return (
          EventCategory.connectivity,
          EventSeverity.critical,
          'Device Offline',
          'Device lost connection',
        );
      case 'connectivity_restored':
        return (
          EventCategory.connectivity,
          EventSeverity.info,
          'Device Online',
          'Device reconnected',
        );
      case 'high_temperature':
        return (
          EventCategory.temperature,
          EventSeverity.warning,
          'High Temperature',
          'Temperature threshold exceeded',
        );
      case 'low_temperature':
        return (
          EventCategory.temperature,
          EventSeverity.warning,
          'Low Temperature',
          'Temperature below threshold',
        );
      case 'light_on':
        return (
          EventCategory.light,
          EventSeverity.info,
          'Light Activated',
          'Light was turned on',
        );
      case 'light_off':
        return (
          EventCategory.light,
          EventSeverity.info,
          'Light Deactivated',
          'Light was turned off',
        );
      default:
        return (
          EventCategory.system,
          EventSeverity.info,
          'Event: $eventType',
          'Event occurred on device',
        );
    }
  }

  /// Parse timestamp from various formats
  DateTime _parseTimestamp(dynamic raw) {
    if (raw == null) return DateTime.now();

    try {
      if (raw is String) {
        return DateTime.parse(raw);
      } else if (raw is int) {
        return DateTime.fromMillisecondsSinceEpoch(raw * 1000);
      } else if (raw is double) {
        return DateTime.fromMillisecondsSinceEpoch((raw * 1000).toInt());
      }
    } catch (e) {
      debugPrint('Failed to parse timestamp: $e');
    }

    return DateTime.now();
  }

  /// Extract tank ID from device ID (e.g., 'tank1' from 'tank1_sensor1')
  String _extractTankIdFromDeviceId(String deviceId) {
    // If device_id contains underscore, use first part as tank ID
    if (deviceId.contains('_')) {
      return deviceId.split('_').first;
    }
    // Otherwise, assume it's a tank ID (e.g., 'tank1')
    return deviceId;
  }

  /// Extract tank name from device ID
  String _extractTankNameFromDeviceId(String deviceId) {
    final tankId = _extractTankIdFromDeviceId(deviceId);
    // Format: 'tank1' -> 'Tank 1', 'water_tank' -> 'Water Tank'
    return tankId
        .replaceAllMapped(RegExp(r'_'), (_) => ' ')
        .split(' ')
        .map((word) => word[0].toUpperCase() + word.substring(1))
        .join(' ');
  }

  /// Acknowledge an event (mark as acknowledged)
  /// Backend updates isAcknowledged flag; client must refetch
  Future<void> acknowledgeEvent(String id) async {
    try {
      await _dio.post('/events/$id/acknowledge');
    } catch (e) {
      throw EventServiceException('Failed to acknowledge event $id: $e');
    }
  }

  /// Mark an event as read (viewed by user)
  /// Backend updates isRead flag; client should refetch or update locally
  Future<void> markEventRead(String id) async {
    try {
      await _dio.post('/events/$id/read');
    } catch (e) {
      throw EventServiceException('Failed to mark event $id as read: $e');
    }
  }

  /// Export events as CSV (Phase 4)
  Future<String> exportEventsAsCSV(List<Event> events) async {
    try {
      // CSV header
      final buffer = StringBuffer();
      buffer.writeln('ID,Tank,Device,Category,Type,Title,Severity,Timestamp,Value,Threshold,IsAcknowledged,IsRead');

      // CSV rows
      for (final event in events) {
        final escapedTitle = event.title.replaceAll('"', '""');
        buffer.writeln(
          '"${event.id}",'
          '"${event.tankName}",'
          '"${event.deviceName ?? ''}",'
          '"${event.category.name}",'
          '"${event.type}",'
          '"$escapedTitle",'
          '"${event.severity.name}",'
          '"${event.timestamp.toIso8601String()}",'
          '"${event.value ?? ''}",'
          '"${event.threshold ?? ''}",'
          '${event.isAcknowledged},'
          '${event.isRead}',
        );
      }

      return buffer.toString();
    } catch (e) {
      throw EventServiceException('Failed to export events as CSV: $e');
    }
  }

  /// Search events (Phase 4)
  Future<List<Event>> searchEvents(String query, {int limit = 50}) async {
    try {
      final response = await _dio.get(
        '/events/search',
        queryParameters: {
          'q': query,
          'limit': limit,
        },
      );

      final eventsList = (response.data as List<dynamic>? ?? [])
          .map((e) {
            try {
              return _mapApiResponseToEvent(e as Map<String, dynamic>);
            } catch (e) {
              debugPrint('Failed to parse search event: $e');
              return null;
            }
          })
          .whereType<Event>()
          .toList();

      return eventsList;
    } catch (e) {
      throw EventServiceException('Failed to search events: $e');
    }
  }
}

class EventServiceException implements Exception {
  final String message;
  EventServiceException(this.message);

  @override
  String toString() => message;
}
