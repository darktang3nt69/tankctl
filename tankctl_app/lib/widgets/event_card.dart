/// Event card widget - displays a single event in the list
library;

import 'package:flutter/material.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';
import 'package:tankctl_app/domain/event.dart';
import 'package:tankctl_app/utils/app_icons.dart';

class EventCard extends StatelessWidget {
  final Event event;
  final VoidCallback onTap;
  final VoidCallback? onAcknowledge;
  final bool isUnread;

  const EventCard({
    super.key,
    required this.event,
    required this.onTap,
    this.onAcknowledge,
    this.isUnread = false,
  });

  /// Get icon for event category
  IconData _getCategoryIcon() {
    return switch (event.category) {
      EventCategory.light => AppIcons.lightOn,
      EventCategory.temperature => AppIcons.thermostat,
      EventCategory.connectivity => AppIcons.wifiStrong,
      EventCategory.system => AppIcons.systemUpdate,
    };
  }

  /// Get color based on severity
  Color _getSeverityColor() {
    return switch (event.severity) {
      EventSeverity.info => TankCtlColors.success,
      EventSeverity.warning => const Color(0xFFFFA76B),
      EventSeverity.critical => TankCtlColors.temperature,
    };
  }

  /// Get background color based on severity (Phase 3 - enhanced)
  Color _getBackgroundColor() {
    return switch (event.severity) {
      EventSeverity.info => TankCtlColors.success.withValues(alpha: 0.08),
      EventSeverity.warning => const Color(0xFFFFA76B).withValues(alpha: 0.12),
      EventSeverity.critical => TankCtlColors.temperature.withValues(alpha: 0.15),
    };
  }

  /// Format timestamp to human-readable string
  String _formatTime() {
    final duration = DateTime.now().difference(event.timestamp);
    if (duration.inSeconds < 60) {
      return '${duration.inSeconds}s ago';
    } else if (duration.inMinutes < 60) {
      return '${duration.inMinutes}m ago';
    } else if (duration.inHours < 24) {
      return '${duration.inHours}h ago';
    } else if (duration.inDays < 7) {
      return '${duration.inDays}d ago';
    } else {
      return '${event.timestamp.month}/${event.timestamp.day}/${event.timestamp.year}';
    }
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final severityColor = _getSeverityColor();
    final backgroundColor = _getBackgroundColor();

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: backgroundColor,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: severityColor.withValues(alpha: 0.3),
            width: 1,
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header row: icon, title, unread dot, acknowledge button
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Category icon
                  Icon(
                    _getCategoryIcon(),
                    color: severityColor,
                    size: 20,
                  ),
                  const SizedBox(width: 8),

                  // Title and tank name
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                event.title,
                                style: textTheme.labelLarge?.copyWith(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w600,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            if (isUnread)
                              Container(
                                width: 8,
                                height: 8,
                                margin: const EdgeInsets.only(left: 8),
                                decoration: BoxDecoration(
                                  color: TankCtlColors.success,
                                  shape: BoxShape.circle,
                                ),
                              ),
                          ],
                        ),
                        const SizedBox(height: 2),
                        Text(
                          event.tankName,
                          style: textTheme.bodySmall?.copyWith(
                            color: Colors.white70,
                            fontSize: 11,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),

                  // Severity badge
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: severityColor,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      event.severity.displayName,
                      style: textTheme.labelSmall?.copyWith(
                        color: Colors.white,
                        fontSize: 10,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 8),

              // Description
              Text(
                event.description,
                style: textTheme.bodySmall?.copyWith(
                  color: Colors.white.withValues(alpha: 0.87),
                  fontSize: 12,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),

              const SizedBox(height: 8),

              // Footer row: timestamp, device, source badge, acknowledge button
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            if (event.deviceName != null)
                              Expanded(
                                child: Text(
                                  event.deviceName!,
                                  style: textTheme.labelSmall?.copyWith(
                                    color: Colors.white54,
                                    fontSize: 10,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            if (event.source != null) ...[
                              if (event.deviceName != null)
                                const SizedBox(width: 4),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 6,
                                  vertical: 2,
                                ),
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: 0.1),
                                  borderRadius: BorderRadius.circular(3),
                                ),
                                child: Text(
                                  event.source!.substring(0, 1).toUpperCase(),
                                  style: textTheme.labelSmall?.copyWith(
                                    color: Colors.white54,
                                    fontSize: 9,
                                  ),
                                ),
                              ),
                            ],
                          ],
                        ),
                        Text(
                          _formatTime(),
                          style: textTheme.labelSmall?.copyWith(
                            color: Colors.white54,
                            fontSize: 10,
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (!event.isAcknowledged &&
                      (event.severity == EventSeverity.warning ||
                          event.severity == EventSeverity.critical) &&
                      onAcknowledge != null)
                    Padding(
                      padding: const EdgeInsets.only(left: 8),
                      child: TextButton(
                        onPressed: onAcknowledge,
                        style: TextButton.styleFrom(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 4,
                          ),
                          minimumSize: Size.zero,
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        ),
                        child: Text(
                          'Ack',
                          style: textTheme.labelSmall?.copyWith(
                            color: severityColor,
                            fontWeight: FontWeight.w600,
                            fontSize: 10,
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
