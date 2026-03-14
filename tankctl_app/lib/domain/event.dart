/// Event domain model for TankCtl
/// Immutable, server-authoritative representation of device activity
library;

import 'package:flutter/foundation.dart';

enum EventSeverity {
  info,
  warning,
  critical;

  String get displayName => switch (this) {
    EventSeverity.info => 'Info',
    EventSeverity.warning => 'Warning',
    EventSeverity.critical => 'Critical',
  };
}

enum EventCategory {
  light,
  temperature,
  connectivity,
  system;

  String get displayName => switch (this) {
    EventCategory.light => 'Light',
    EventCategory.temperature => 'Temperature',
    EventCategory.connectivity => 'Connectivity',
    EventCategory.system => 'System',
  };
}

@immutable
class Event {
  final String id;
  final String tankId;
  final String tankName;
  final String? deviceId;
  final String? deviceName;
  final EventCategory category;
  final String type; // e.g., 'high_temp_warning', 'light_on', 'device_offline'
  final String title;
  final String description;
  final EventSeverity severity;
  final DateTime timestamp;
  final dynamic value; // e.g., 29.8 for temperature
  final dynamic threshold; // e.g., 28.0 for threshold
  final String? source; // 'device', 'app', 'backend', 'automation'
  final bool isAcknowledged;
  final bool isRead;

  const Event({
    required this.id,
    required this.tankId,
    required this.tankName,
    this.deviceId,
    this.deviceName,
    required this.category,
    required this.type,
    required this.title,
    required this.description,
    required this.severity,
    required this.timestamp,
    this.value,
    this.threshold,
    this.source,
    this.isAcknowledged = false,
    this.isRead = false,
  });

  /// Parse from backend JSON response
  factory Event.fromJson(Map<String, dynamic> json) {
    // Safely parse category, defaulting to 'system' if null or invalid
    final categoryStr = (json['category'] as String?) ?? 'system';
    final category = EventCategory.values.firstWhere(
      (e) => e.name == categoryStr.toLowerCase(),
      orElse: () => EventCategory.system,
    );

    // Safely parse severity, defaulting to 'info' if null or invalid
    final severityStr = (json['severity'] as String?) ?? 'info';
    final severity = EventSeverity.values.firstWhere(
      (e) => e.name == severityStr.toLowerCase(),
      orElse: () => EventSeverity.info,
    );

    // Safely parse timestamp, defaulting to now if null or invalid
    DateTime timestamp;
    try {
      final timestampStr = json['timestamp'] as String?;
      timestamp = timestampStr != null ? DateTime.parse(timestampStr) : DateTime.now();
    } catch (e) {
      timestamp = DateTime.now();
    }

    return Event(
      id: (json['id'] as String?) ?? 'unknown',
      tankId: (json['tankId'] as String?) ?? 'unknown',
      tankName: (json['tankName'] as String?) ?? 'Unknown Tank',
      deviceId: json['deviceId'] as String?,
      deviceName: json['deviceName'] as String?,
      category: category,
      type: (json['type'] as String?) ?? 'generic',
      title: (json['title'] as String?) ?? 'Event',
      description: (json['description'] as String?) ?? 'No description',
      severity: severity,
      timestamp: timestamp,
      value: json['value'],
      threshold: json['threshold'],
      source: json['source'] as String?,
      isAcknowledged: json['isAcknowledged'] as bool? ?? false,
      isRead: json['isRead'] as bool? ?? false,
    );
  }

  /// Convert to JSON for API calls
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'tankId': tankId,
      'tankName': tankName,
      'deviceId': deviceId,
      'deviceName': deviceName,
      'category': category.name,
      'type': type,
      'title': title,
      'description': description,
      'severity': severity.name,
      'timestamp': timestamp.toIso8601String(),
      'value': value,
      'threshold': threshold,
      'source': source,
      'isAcknowledged': isAcknowledged,
      'isRead': isRead,
    };
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Event &&
          runtimeType == other.runtimeType &&
          id == other.id;

  @override
  int get hashCode => id.hashCode;
}

/// Filter state for events (ephemeral, client-side only, not persisted)
@immutable
class EventFilter {
  final String? tankId;
  final EventCategory? category;
  final EventSeverity? severity;
  final DateTime? fromDate;
  final DateTime? toDate;
  final String sortOrder; // 'newest' (default), 'oldest', 'severity'
  final String? searchQuery;
  final bool showAcknowledged;

  const EventFilter({
    this.tankId,
    this.category,
    this.severity,
    this.fromDate,
    this.toDate,
    this.sortOrder = 'newest',
    this.searchQuery,
    this.showAcknowledged = true,
  });

  EventFilter copyWith({
    String? tankId,
    EventCategory? category,
    EventSeverity? severity,
    DateTime? fromDate,
    DateTime? toDate,
    String? sortOrder,
    String? searchQuery,
    bool? showAcknowledged,
  }) {
    return EventFilter(
      tankId: tankId ?? this.tankId,
      category: category ?? this.category,
      severity: severity ?? this.severity,
      fromDate: fromDate ?? this.fromDate,
      toDate: toDate ?? this.toDate,
      sortOrder: sortOrder ?? this.sortOrder,
      searchQuery: searchQuery ?? this.searchQuery,
      showAcknowledged: showAcknowledged ?? this.showAcknowledged,
    );
  }

  /// Check if any filters are active
  bool get hasActiveFilters =>
      tankId != null ||
      category != null ||
      severity != null ||
      fromDate != null ||
      toDate != null ||
      searchQuery != null ||
      !showAcknowledged;

  /// Reset all filters
  EventFilter reset() => const EventFilter();
}
