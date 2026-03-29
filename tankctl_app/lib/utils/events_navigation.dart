// This file has been deleted as part of dead code cleanup.
// All factory methods and static helpers were unused.

class EventsScreenNavigation {
  /// Tank ID to pre-filter events
  final String? tankId;

  /// Tank name for display
  final String? tankName;

  /// Event severity to pre-filter ('info', 'warning', 'critical')
  final String? severity;

  /// Event category to pre-filter ('light', 'temperature', 'connectivity', 'system')
  final String? category;

  /// Incident ID to highlight
  final String? incidentId;

  /// Search query to apply
  final String? searchQuery;

  EventsScreenNavigation({
    this.tankId,
    this.tankName,
    this.severity,
    this.category,
    this.incidentId,
    this.searchQuery,
  });

  /// Create from warning/alert tap (e.g., dashboard warning card)
  factory EventsScreenNavigation.fromWarning({
    required String tankId,
    required String tankName,
    String? category,
  }) {
    return EventsScreenNavigation(
      tankId: tankId,
      tankName: tankName,
      severity: 'warning',
      category: category,
    );
  }

  /// Create from critical alert
  factory EventsScreenNavigation.fromCriticalAlert({
    required String tankId,
    required String tankName,
    String? category,
  }) {
    return EventsScreenNavigation(
      tankId: tankId,
      tankName: tankName,
      severity: 'critical',
      category: category,
    );
  }

  /// Create for viewing incident
  factory EventsScreenNavigation.fromIncident({
    required String incidentId,
  }) {
    return EventsScreenNavigation(incidentId: incidentId);
  }
}

/// Helper to navigate to Events screen with pre-applied filters
class EventsNavigationHelper {
  /// Navigate to Events screen with filter state
  static Future<void> navigate(
    BuildContext context,
    EventsScreenNavigation params, {
    bool replace = false,
  }) {
    // Using Navigator.push (adjust for your routing setup)
    // If using GoRouter, replace this with your router.push() call
    if (replace) {
      return Navigator.of(context).pushReplacementNamed(
        '/events',
        arguments: params,
      );
    } else {
      return Navigator.of(context).pushNamed(
        '/events',
        arguments: params,
      );
    }
  }

  /// Navigate from dashboard warning to Events
  static Future<void> navigateFromDashboardWarning(
    BuildContext context, {
    required String tankId,
    required String tankName,
    String? category,
  }) {
    return navigate(
      context,
      EventsScreenNavigation.fromWarning(
        tankId: tankId,
        tankName: tankName,
        category: category,
      ),
    );
  }

  /// Navigate from dashboard critical alert
  static Future<void> navigateFromDashboardCritical(
    BuildContext context, {
    required String tankId,
    required String tankName,
    String? category,
  }) {
    return navigate(
      context,
      EventsScreenNavigation.fromCriticalAlert(
        tankId: tankId,
        tankName: tankName,
        category: category,
      ),
    );
  }

  /// Example usage in dashboard widget:
  /// ```
  /// GestureDetector(
  ///   onTap: () {
  ///     EventsNavigationHelper.navigateFromDashboardWarning(
  ///       context,
  ///       tankId: 'tank_001',
  ///       tankName: 'Main Tank',
  ///       category: 'temperature',
  ///     );
  ///   },
  ///   child: WarningCard(...),
  /// )
  /// ```
}

/// Extension to easily apply navigation params to filter state
extension EventsNavigationFilterExt on EventsScreenNavigation {
  /// Apply navigation parameters to filter state
  Map<String, String> toFilterState() {
    return {
      'tankId': ?tankId,
      'tankName': ?tankName,
      'severity': ?severity,
      'category': ?category,
      'incidentId': ?incidentId,
      'searchQuery': ?searchQuery,
    };
  }

  /// Get display name for breadcrumb/header
  String get displayLabel {
    if (severity != null && tankName != null) {
      return '$severity events for $tankName';
    } else if (tankName != null) {
      return 'Events for $tankName';
    } else if (incidentId != null) {
      return 'Incident Events';
    }
    return 'Events';
  }
}
