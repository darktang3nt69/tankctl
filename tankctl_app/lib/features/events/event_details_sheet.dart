/// Event details sheet (Phase 2) - shows full event context in a bottom sheet
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';
import 'package:tankctl_app/domain/event.dart';
import 'package:tankctl_app/utils/app_icons.dart';

class EventDetailsSheet extends ConsumerStatefulWidget {
  final Event event;

  const EventDetailsSheet({
    super.key,
    required this.event,
  });

  @override
  ConsumerState<EventDetailsSheet> createState() => _EventDetailsSheetState();
}

class _EventDetailsSheetState extends ConsumerState<EventDetailsSheet> {
  /// Get icon for severity
  IconData _getSeverityIcon() {
    return switch (widget.event.severity) {
      EventSeverity.info => AppIcons.info,
      EventSeverity.warning => AppIcons.warning,
      EventSeverity.critical => AppIcons.error,
    };
  }

  /// Get color based on severity
  Color _getSeverityColor() {
    return switch (widget.event.severity) {
      EventSeverity.info => TankCtlColors.success,
      EventSeverity.warning => const Color(0xFFFFA76B),
      EventSeverity.critical => TankCtlColors.temperature,
    };
  }

  /// Format timestamp to human-readable string
  String _formatFullTime() {
    final formatter = widget.event.timestamp;
    final now = DateTime.now();
    final daysAgo = now.difference(formatter).inDays;

    final timeStr =
        '${formatter.hour.toString().padLeft(2, '0')}:${formatter.minute.toString().padLeft(2, '0')}';
    final dateStr =
        '${formatter.month}/${formatter.day}/${formatter.year}';

    if (daysAgo == 0) {
      return 'Today at $timeStr';
    } else if (daysAgo == 1) {
      return 'Yesterday at $timeStr';
    } else {
      return '$dateStr at $timeStr';
    }
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final severityColor = _getSeverityColor();

    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.6,
      minChildSize: 0.4,
      maxChildSize: 0.9,
      builder: (context, scrollController) {
        return Container(
          decoration: const BoxDecoration(
            color: Color(0xFF1A1A1A),
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(16),
              topRight: Radius.circular(16),
            ),
          ),
          child: ListView(
            controller: scrollController,
            padding: const EdgeInsets.all(16),
            children: [
              // Header with close button
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(
                              _getSeverityIcon(),
                              color: severityColor,
                              size: 24,
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                widget.event.title,
                                style: textTheme.titleLarge?.copyWith(
                                  fontWeight: FontWeight.w700,
                                ),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: severityColor.withValues(alpha: 0.2),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            widget.event.severity.displayName,
                            style: textTheme.labelSmall?.copyWith(
                              color: severityColor,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),

              const Divider(height: 24, thickness: 0.5),

              // Description
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Description',
                    style: textTheme.labelLarge?.copyWith(
                      color: Colors.white70,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    widget.event.description,
                    style: textTheme.bodyMedium?.copyWith(
                      color: Colors.white.withValues(alpha: 0.87),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 16),

              // Location info (tank & device)
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Location',
                    style: textTheme.labelLarge?.copyWith(
                      color: Colors.white70,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.05),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Tank',
                          style: textTheme.labelSmall?.copyWith(
                            color: Colors.white54,
                          ),
                        ),
                        Text(
                          widget.event.tankName,
                          style: textTheme.bodyMedium?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        if (widget.event.deviceName != null) ...[
                          const SizedBox(height: 8),
                          Text(
                            'Device',
                            style: textTheme.labelSmall?.copyWith(
                              color: Colors.white54,
                            ),
                          ),
                          Text(
                            widget.event.deviceName!,
                            style: textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 16),

              // Event details
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Details',
                    style: textTheme.labelLarge?.copyWith(
                      color: Colors.white70,
                    ),
                  ),
                  const SizedBox(height: 8),
                  _DetailRow(
                    label: 'Category',
                    value: widget.event.category.displayName,
                    textTheme: textTheme,
                  ),
                  _DetailRow(
                    label: 'Type',
                    value: widget.event.type,
                    textTheme: textTheme,
                  ),
                  _DetailRow(
                    label: 'Time',
                    value: _formatFullTime(),
                    textTheme: textTheme,
                  ),
                  if (widget.event.source != null)
                    _DetailRow(
                      label: 'Source',
                      value: widget.event.source!,
                      textTheme: textTheme,
                    ),
                  if (widget.event.value != null)
                    _DetailRow(
                      label: 'Value',
                      value: '${widget.event.value}',
                      textTheme: textTheme,
                    ),
                  if (widget.event.threshold != null)
                    _DetailRow(
                      label: 'Threshold',
                      value: '${widget.event.threshold}',
                      textTheme: textTheme,
                    ),
                ],
              ),

              const SizedBox(height: 16),
            ],
          ),
        );
      },
    );
  }
}

/// Detail row widget
class _DetailRow extends StatelessWidget {
  final String label;
  final String value;
  final TextTheme textTheme;

  const _DetailRow({
    required this.label,
    required this.value,
    required this.textTheme,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(
              label,
              style: textTheme.labelSmall?.copyWith(
                color: Colors.white54,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: textTheme.bodySmall?.copyWith(
                color: Colors.white.withValues(alpha: 0.87),
              ),
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
