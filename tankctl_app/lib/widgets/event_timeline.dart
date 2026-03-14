/// Event timeline widget (Phase 2) - displays events grouped by date
library;

import 'package:flutter/material.dart';
import 'package:tankctl_app/domain/event.dart';
import 'package:tankctl_app/widgets/event_card.dart';

class EventTimeline extends StatelessWidget {
  final Map<String, List<Event>> groupedEvents;
  final void Function(Event) onEventTap;
  final void Function(String)? onAcknowledge;

  const EventTimeline({
    super.key,
    required this.groupedEvents,
    required this.onEventTap,
    this.onAcknowledge,
  });

  /// Order for time group keys
  static const _groupOrder = ['Today', 'Yesterday', 'Earlier this week', 'Older'];

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    // Sort groups by defined order
    final sortedGroups = <String, List<Event>>{};
    for (final key in _groupOrder) {
      if (groupedEvents.containsKey(key)) {
        sortedGroups[key] = groupedEvents[key]!;
      }
    }

    return ListView.builder(
      itemCount: sortedGroups.length,
      itemBuilder: (context, groupIndex) {
        final groupKey = sortedGroups.keys.elementAt(groupIndex);
        final events = sortedGroups[groupKey]!;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Group header
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Row(
                children: [
                  Text(
                    groupKey,
                    style: textTheme.labelLarge?.copyWith(
                      color: Colors.white54,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 0.2,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 2,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '${events.length}',
                      style: textTheme.labelSmall?.copyWith(
                        color: Colors.white54,
                        fontSize: 11,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // Events in group
            ...events.map((event) {
              final isUnread = !event.isRead;
              return EventCard(
                event: event,
                isUnread: isUnread,
                onTap: () => onEventTap(event),
                onAcknowledge: onAcknowledge != null
                    ? () => onAcknowledge!(event.id)
                    : null,
              );
            }),

            // Divider between groups
            if (groupIndex < sortedGroups.length - 1)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 12),
                child: Divider(
                  height: 0.5,
                  thickness: 0.5,
                  color: Colors.white.withValues(alpha: 0.1),
                ),
              ),
          ],
        );
      },
    );
  }
}
