import '../domain/event.dart';

/// Event correlation and incident grouping service
class EventCorrelationService {
  /// Find related events (same device, similar category, within time window)
  static List<Event> findRelatedEvents(
    Event event,
    List<Event> allEvents, {
    Duration timeWindow = const Duration(hours: 6),
  }) {
    final eventTime = event.timestamp;
    final windowStart = eventTime.subtract(timeWindow);
    final windowEnd = eventTime.add(timeWindow);

    return allEvents
        .where((e) {
          if (e.id == event.id) return false; // Exclude self

          final eTime = e.timestamp;

          // Same device + same general category + within time window
          return e.deviceId == event.deviceId &&
              e.category == event.category &&
              eTime.isAfter(windowStart) &&
              eTime.isBefore(windowEnd);
        })
        .toList()
      ..sort((a, b) => b.timestamp.compareTo(a.timestamp)); // Newest first
  }

  /// Group related events into incidents (chains of related events)
  static List<EventIncident> groupIntoIncidents(List<Event> events) {
    final incidents = <EventIncident>[];
    final processed = <String>{};

    for (final event in events) {
      if (processed.contains(event.id)) continue;

      // Find chain of related events
      final chain = _buildIncidentChain(event, events);
      if (chain.isNotEmpty) {
        incidents.add(
          EventIncident(
            id: _generateIncidentId(chain),
            events: chain,
            severity: _getChainSeverity(chain),
            category: chain.first.category.displayName,
            tankId: chain.first.tankId,
            deviceId: chain.first.deviceId,
          ),
        );

        // Mark all as processed
        for (final e in chain) {
          processed.add(e.id);
        }
      }
    }

    return incidents;
  }

  /// Build incident chain for connectivity issues (offline → online → resume)
  static List<Event> _buildIncidentChain(
    Event startEvent,
    List<Event> allEvents,
  ) {
    if (startEvent.category != EventCategory.connectivity) {
      // For non-connectivity, just return the single event
      return [startEvent];
    }

    final chain = <Event>[startEvent];
    final startTime = startEvent.timestamp;

    // Look for related connectivity events within 1 hour
    final relatedEvents = allEvents
        .where((e) {
          if (e.id == startEvent.id) return false;
          if (e.category != EventCategory.connectivity) return false;
          if (e.deviceId == null || startEvent.deviceId == null) return false;
          if (e.deviceId != startEvent.deviceId) return false;

          final eTime = e.timestamp;
          final diff = eTime.difference(startTime).abs();
          return diff.inHours <= 1;
        })
        .toList()
      ..sort((a, b) => a.timestamp.compareTo(b.timestamp));

    chain.addAll(relatedEvents);
    return chain;
  }

  static String _generateIncidentId(List<Event> chain) {
    if (chain.isEmpty) return '';
    final first = chain.first;
    final last = chain.last;
    return '${first.deviceId}_${first.category.name}_${first.timestamp.millisecondsSinceEpoch}_${last.timestamp.millisecondsSinceEpoch}';
  }

  static String _getChainSeverity(List<Event> chain) {
    // Return highest severity in chain
    if (chain.any((e) => e.severity == EventSeverity.critical)) {
      return 'critical';
    } else if (chain.any((e) => e.severity == EventSeverity.warning)) {
      return 'warning';
    }
    return 'info';
  }

  /// Check if event is part of an incident
  static bool isPartOfIncident(Event event, List<EventIncident> incidents) {
    return incidents.any((incident) =>
        incident.events.any((e) => e.id == event.id));
  }

  /// Get incident containing this event
  static EventIncident? getEventIncident(
    Event event,
    List<EventIncident> incidents,
  ) {
    try {
      return incidents.firstWhere(
        (incident) => incident.events.any((e) => e.id == event.id),
      );
    } catch (e) {
      return null;
    }
  }
}

/// Represents a group of related events (e.g., device offline → online → resumed)
class EventIncident {
  final String id;
  final List<Event> events;
  final String severity;
  final String category;
  final String tankId;
  final String? deviceId;

  EventIncident({
    required this.id,
    required this.events,
    required this.severity,
    required this.category,
    required this.tankId,
    this.deviceId,
  });

  /// Get human-readable incident summary
  String get summary {
    if (events.isEmpty) return 'Unknown incident';
    if (category.toLowerCase() == 'connectivity') {
      // e.g., "3 events: Device went offline, came back online, resumed operation"
      return '${events.length} connectivity events: ${_buildConnectivitySummary()}';
    }
    return '${events.length} ${category.toLowerCase()} events';
  }

  String _buildConnectivitySummary() {
    final titles = events.map((e) => e.title).join(' → ');
    return titles;
  }

  /// Duration of incident
  Duration get duration {
    if (events.length < 2) return Duration.zero;
    final first = events.first.timestamp;
    final last = events.last.timestamp;
    return last.difference(first);
  }
}
