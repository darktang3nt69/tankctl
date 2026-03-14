import 'package:flutter/material.dart';
import '../domain/event.dart';
import '../services/event_correlation_service.dart';

/// Widget displaying related events in the detail sheet
class RelatedEventsWidget extends StatelessWidget {
  final Event event;
  final List<Event> allEvents;
  final VoidCallback? onRelatedEventTap;

  const RelatedEventsWidget({
    super.key,
    required this.event,
    required this.allEvents,
    this.onRelatedEventTap,
  });

  @override
  Widget build(BuildContext context) {
    final relatedEvents =
        EventCorrelationService.findRelatedEvents(event, allEvents);

    if (relatedEvents.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Related Events',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: Colors.grey[600],
                  letterSpacing: 0.5,
                ),
              ),
              const SizedBox(height: 12),
              Container(
                decoration: BoxDecoration(
                  color: Colors.purple[50],
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.purple[200]!),
                ),
                child: Column(
                  children: List.generate(
                    relatedEvents.length,
                    (index) {
                      final relatedEvent = relatedEvents[index];
                      return Column(
                        children: [
                          _buildRelatedEventTile(
                            context,
                            relatedEvent,
                            isFirst: index == 0,
                          ),
                          if (index < relatedEvents.length - 1)
                            Divider(
                              height: 1,
                              color: Colors.purple[200],
                              indent: 16,
                              endIndent: 16,
                            ),
                        ],
                      );
                    },
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
      ],
    );
  }

  Widget _buildRelatedEventTile(
    BuildContext context,
    Event event,
    {bool isFirst = false}
  ) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onRelatedEventTap,
        child: Padding(
          padding: EdgeInsets.fromLTRB(
            12,
            isFirst ? 12 : 8,
            12,
            8,
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Icon(
                _getEventIcon(event.category),
                size: 16,
                color: Colors.purple[600],
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      event.title,
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      _formatTime(event.timestamp),
                      style: TextStyle(
                        fontSize: 11,
                        color: Colors.grey[500],
                      ),
                    ),
                  ],
                ),
              ),
              Icon(
                Icons.arrow_forward_ios,
                size: 12,
                color: Colors.grey[400],
              ),
            ],
          ),
        ),
      ),
    );
  }

  IconData _getEventIcon(EventCategory category) {
    return switch (category) {
      EventCategory.light => Icons.lightbulb_outline,
      EventCategory.temperature => Icons.opacity,
      EventCategory.connectivity => Icons.wifi,
      EventCategory.system => Icons.settings,
    };
  }

  String _formatTime(DateTime timestamp) {
    try {
      return '${timestamp.hour}:${timestamp.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return 'Unknown';
    }
  }
}

/// Incident summary widget for multiple related events
class IncidentSummaryWidget extends StatelessWidget {
  final EventIncident incident;
  final VoidCallback? onViewIncident;

  const IncidentSummaryWidget({
    super.key,
    required this.incident,
    this.onViewIncident,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16.0),
      decoration: BoxDecoration(
        color: _getIncidentColor().withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: _getIncidentColor().withValues(alpha: 0.3),
          width: 1,
        ),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: onViewIncident,
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  Icons.link,
                  color: _getIncidentColor(),
                  size: 20,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Part of Incident',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: _getIncidentColor(),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        incident.summary,
                        style: TextStyle(
                          fontSize: 12,
                          color: _getIncidentColor().withValues(alpha: 0.8),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Duration: ${_formatDuration(incident.duration)}',
                        style: TextStyle(
                          fontSize: 11,
                          color: _getIncidentColor().withValues(alpha: 0.6),
                        ),
                      ),
                    ],
                  ),
                ),
                Icon(
                  Icons.chevron_right,
                  color: _getIncidentColor().withValues(alpha: 0.5),
                  size: 18,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Color _getIncidentColor() {
    switch (incident.severity.toLowerCase()) {
      case 'critical':
        return Colors.red;
      case 'warning':
        return Colors.orange;
      default:
        return Colors.blue;
    }
  }

  String _formatDuration(Duration duration) {
    if (duration.inSeconds < 60) {
      return '${duration.inSeconds}s';
    } else if (duration.inMinutes < 60) {
      return '${duration.inMinutes}m';
    } else {
      return '${duration.inHours}h ${duration.inMinutes % 60}m';
    }
  }
}
