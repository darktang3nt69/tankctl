import 'package:flutter/material.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';

enum AttentionIssueType { offline, noTempSensor, highTemp, lowTemp }

class AttentionIssue {
  const AttentionIssue({
    required this.deviceId,
    required this.deviceLabel,
    required this.type,
    this.temperature,
  });

  final String deviceId;
  final String deviceLabel;
  final AttentionIssueType type;
  final double? temperature;
}

class NeedsAttentionStrip extends StatelessWidget {
  const NeedsAttentionStrip({
    super.key,
    required this.issues,
    required this.onTapIssue,
  });

  final List<AttentionIssue> issues;
  final ValueChanged<String> onTapIssue;

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
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: issues.map((issue) {
              final (label, icon, color) = _meta(issue);
              return ActionChip(
                onPressed: () => onTapIssue(issue.deviceId),
                avatar: Icon(icon, size: 16, color: color),
                side: BorderSide(color: color.withValues(alpha: 0.45)),
                backgroundColor: color.withValues(alpha: 0.12),
                label: Text(
                  label,
                  style: textTheme.labelMedium?.copyWith(
                    color: color,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}
