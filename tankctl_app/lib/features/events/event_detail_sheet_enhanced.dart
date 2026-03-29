// This file has been deleted as part of dead code cleanup.
// Use features/events/event_details_sheet.dart instead.


/// Enhanced Event Detail Sheet with related events and incident grouping
class EventDetailSheetEnhanced extends StatelessWidget {
  final Event event;
  final List<Event> allEvents;
  final Function(Event)? onRelatedEventTap;

  const EventDetailSheetEnhanced({
    super.key,
    required this.event,
    this.allEvents = const [],
    this.onRelatedEventTap,
  });

  static Future<void> show(
    BuildContext context,
    Event event, {
    List<Event> allEvents = const [],
    Function(Event)? onRelatedEventTap,
  }) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (context) => EventDetailSheetEnhanced(
        event: event,
        allEvents: allEvents,
        onRelatedEventTap: onRelatedEventTap,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final incidents = EventCorrelationService.groupIntoIncidents(allEvents);
    final eventIncident = EventCorrelationService.getEventIncident(
      event,
      incidents,
    );
    final hasIncident = eventIncident != null && eventIncident.events.isNotEmpty;

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.9,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Handle bar
            Padding(
              padding: const EdgeInsets.only(top: 12.0, bottom: 16.0),
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey[300],
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            // Header with icon and title
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: _getSeverityColor(event.severity).withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(
                      _getEventIcon(event.category),
                      color: _getSeverityColor(event.severity),
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          event.title,
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          _formatTimestamp(event.timestamp),
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: _getSeverityColor(event.severity).withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                        color: _getSeverityColor(event.severity),
                        width: 1,
                      ),
                    ),
                    child: Text(
                      event.severity.displayName.toUpperCase(),
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: _getSeverityColor(event.severity),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            // Divider
            Divider(height: 1, color: Colors.grey[200]),
            const SizedBox(height: 16),
            // Main description
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Description',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: Colors.grey[600],
                      letterSpacing: 0.5,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    event.description,
                    style: const TextStyle(
                      fontSize: 14,
                      height: 1.5,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            // Incident badge (if part of incident)
            if (hasIncident && eventIncident.events.length > 1)
              Column(
                children: [
                  IncidentSummaryWidget(
                    incident: eventIncident,
                  ),
                  const SizedBox(height: 16),
                ],
              ),
            // Device & Tank Info
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0),
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.grey[50],
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey[200]!),
                ),
                child: Column(
                  children: [
                    _buildDetailRow(
                      'Tank',
                      event.tankName,
                      isFirst: true,
                    ),
                    if (event.deviceName != null) ...[
                      Divider(
                        height: 1,
                        color: Colors.grey[200],
                        indent: 16,
                        endIndent: 16,
                      ),
                      _buildDetailRow('Device', event.deviceName!),
                    ],
                    Divider(
                      height: 1,
                      color: Colors.grey[200],
                      indent: 16,
                      endIndent: 16,
                    ),
                    _buildDetailRow('Category', _formatCategory(event.category)),
                    Divider(
                      height: 1,
                      color: Colors.grey[200],
                      indent: 16,
                      endIndent: 16,
                    ),
                    _buildDetailRow(
                      'Source',
                      _formatSource(event.source),
                      isLast: true,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            // Value & Threshold (if applicable)
            if (event.value != null || event.threshold != null)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16.0),
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.blue[50],
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.blue[200]!),
                  ),
                  child: Column(
                    children: [
                      if (event.value != null)
                        _buildDetailRow(
                          'Current Value',
                          event.value.toString(),
                          isFirst: true,
                        ),
                      if (event.value != null && event.threshold != null)
                        Divider(
                          height: 1,
                          color: Colors.blue[200],
                          indent: 16,
                          endIndent: 16,
                        ),
                      if (event.threshold != null)
                        _buildDetailRow(
                          'Threshold',
                          event.threshold.toString(),
                          isLast: event.threshold != null && event.value == null,
                        ),
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 16),
            // Suggested Action (if applicable for critical/warning)
            if (event.severity != EventSeverity.info)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16.0),
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.orange[50],
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.orange[200]!),
                  ),
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        Icons.lightbulb_outline,
                        color: Colors.orange[700],
                        size: 20,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Suggested Action',
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: Colors.orange[900],
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              _getSuggestedAction(event),
                              style: TextStyle(
                                fontSize: 13,
                                color: Colors.orange[800],
                                height: 1.4,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 16),
            // Related Events
            if (allEvents.isNotEmpty)
              RelatedEventsWidget(
                event: event,
                allEvents: allEvents,
                onRelatedEventTap: () {
                  final related =
                      EventCorrelationService.findRelatedEvents(event, allEvents);
                  if (related.isNotEmpty && onRelatedEventTap != null) {
                    onRelatedEventTap!(related.first);
                    Navigator.of(context).pop();
                  }
                },
              ),
            // Event ID (technical detail)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0),
              child: Text(
                'Event ID: ${event.id}',
                style: TextStyle(
                  fontSize: 11,
                  color: Colors.grey[500],
                  fontFamily: 'monospace',
                  letterSpacing: 0,
                ),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(
    String label,
    String value, {
    bool isFirst = false,
    bool isLast = false,
  }) {
    return Padding(
      padding: EdgeInsets.fromLTRB(
        16,
        isFirst ? 12 : 8,
        16,
        isLast ? 12 : 8,
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(
              label,
              style: TextStyle(
                fontSize: 13,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              value,
              textAlign: TextAlign.right,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Color _getSeverityColor(EventSeverity severity) {
    switch (severity) {
      case EventSeverity.critical:
        return Colors.red;
      case EventSeverity.warning:
        return Colors.orange;
      case EventSeverity.info:
        return Colors.blue;
    }
  }

  IconData _getEventIcon(EventCategory category) {
    switch (category) {
      case EventCategory.light:
        return Icons.lightbulb_outline;
      case EventCategory.temperature:
        return Icons.opacity;
      case EventCategory.connectivity:
        return Icons.wifi;
      case EventCategory.system:
        return Icons.settings;
    }
  }

  String _formatTimestamp(DateTime timestamp) {
    try {
      final now = DateTime.now();
      final today = DateTime(now.year, now.month, now.day);
      final eventDate = DateTime(timestamp.year, timestamp.month, timestamp.day);
      
      String dateStr;
      if (eventDate == today) {
        dateStr = 'Today';
      } else if (eventDate == today.subtract(const Duration(days: 1))) {
        dateStr = 'Yesterday';
      } else {
        dateStr = '${timestamp.month}/${timestamp.day}/${timestamp.year}';
      }
      
      return '$dateStr at ${timestamp.hour}:${timestamp.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return 'Unknown';
    }
  }

  String _formatCategory(EventCategory category) {
    return category.displayName;
  }

  String _formatSource(String? source) {
    if (source == null) return 'Unknown';
    switch (source.toLowerCase()) {
      case 'device':
        return 'Device Report';
      case 'app':
        return 'Mobile App';
      case 'backend':
        return 'Server';
      case 'automation':
        return 'Automation Rule';
      default:
        return source;
    }
  }

  String _getSuggestedAction(Event event) {
    if (event.category == EventCategory.temperature) {
      if (event.severity == EventSeverity.critical) {
        return 'Immediately check heater/cooler status. Verify water circulation and room temperature. If critical threshold exceeded, consider emergency cooling/heating.';
      } else {
        return 'Monitor temperature closely. Adjust heater/cooler settings if needed. Check for ambient room temperature changes.';
      }
    } else if (event.category == EventCategory.connectivity) {
      if (event.severity == EventSeverity.critical) {
        return 'Device offline for extended period. Check device power, network connection, and WiFi signal strength. Restart device if necessary.';
      } else {
        return 'Device briefly disconnected. This may resolve automatically. If persists, verify network stability.';
      }
    } else if (event.category == EventCategory.light) {
      return 'Light control executed successfully. Next scheduled toggle: check automation rules if unexpected.';
    } else {
      return 'Review system logs for more details. Contact support if issue persists.';
    }
  }
}
