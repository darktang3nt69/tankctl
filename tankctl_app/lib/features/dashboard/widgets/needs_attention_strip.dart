import 'package:flutter/material.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';

enum AttentionIssueType { offline, noTempSensor, highTemp, lowTemp }

class AttentionIssue {
  const AttentionIssue({
    required this.deviceId,
    required this.deviceLabel,
    required this.type,
    required this.warningCode,
    this.temperature,
  });

  final String deviceId;
  final String deviceLabel;
  final AttentionIssueType type;
  final String warningCode;
  final double? temperature;

  String get issueKey => '${deviceId}_$warningCode';
  String get issueTypeName => warningCode;
}

class NoAttentionBanner extends StatelessWidget {
  const NoAttentionBanner({super.key});

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 14),
      decoration: BoxDecoration(
        color: TankCtlColors.card,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF5BBFA0).withValues(alpha: 0.35)),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.check_circle_rounded,
            color: Color(0xFF5BBFA0),
            size: 18,
          ),
          const SizedBox(width: 10),
          Text(
            'All tanks are stable. No attention needed.',
            style: textTheme.bodyMedium?.copyWith(
              color: const Color(0xFF8BE0C2),
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class NeedsAttentionStrip extends StatefulWidget {
  const NeedsAttentionStrip({
    super.key,
    required this.issues,
    required this.onTapIssue,
    required this.onDismissIssue,
  });

  final List<AttentionIssue> issues;
  final ValueChanged<String> onTapIssue;
  final ValueChanged<AttentionIssue> onDismissIssue;

  @override
  State<NeedsAttentionStrip> createState() => _NeedsAttentionStripState();
}

class _NeedsAttentionStripState extends State<NeedsAttentionStrip> {
  final ScrollController _scrollController = ScrollController();

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  (String, IconData, Color) _meta(AttentionIssue issue) => switch (issue.type) {
        AttentionIssueType.offline => (
          '${issue.deviceLabel} · Offline',
          Icons.cloud_off_rounded,
          Colors.white70,
        ),
        AttentionIssueType.noTempSensor => (
          '${issue.deviceLabel} · No Temp Sensor',
          Icons.sensors_off_rounded,
          const Color(0xFFFFA726),
        ),
        AttentionIssueType.highTemp => (
          '${issue.deviceLabel} · High ${issue.temperature?.toStringAsFixed(1)}°C',
          Icons.thermostat_rounded,
          TankCtlColors.temperature,
        ),
        AttentionIssueType.lowTemp => (
          '${issue.deviceLabel} · Low ${issue.temperature?.toStringAsFixed(1)}°C',
          Icons.ac_unit_rounded,
          const Color(0xFF93C5FD),
        ),
      };

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: TankCtlColors.card,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFFFA726).withValues(alpha: 0.35)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'NEEDS ATTENTION',
            style: textTheme.labelSmall?.copyWith(
              color: const Color(0xFFFFC58A),
              letterSpacing: 1.2,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 8),
          Scrollbar(
            controller: _scrollController,
            thumbVisibility: true,
            child: SingleChildScrollView(
              controller: _scrollController,
              scrollDirection: Axis.horizontal,
              child: Row(
                children: widget.issues.map((issue) {
              final (label, icon, color) = _meta(issue);
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: InkWell(
                      borderRadius: BorderRadius.circular(20),
                      onTap: () => widget.onTapIssue(issue.deviceId),
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: color.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: color.withValues(alpha: 0.45)),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(icon, size: 16, color: color),
                            const SizedBox(width: 6),
                            Text(
                              label,
                              style: textTheme.labelMedium?.copyWith(
                                color: color,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(width: 4),
                            InkWell(
                              borderRadius: BorderRadius.circular(10),
                              onTap: () => widget.onDismissIssue(issue),
                              child: Padding(
                                padding: const EdgeInsets.all(2),
                                child: Icon(
                                  Icons.close_rounded,
                                  size: 14,
                                  color: color,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Swipe horizontally for more issues',
            style: textTheme.labelSmall?.copyWith(
              color: Colors.white38,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}
