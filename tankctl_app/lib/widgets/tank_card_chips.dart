import 'package:flutter/material.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';
import 'package:tankctl_app/widgets/tank_card_helpers.dart';

class TankStatusChip extends StatelessWidget {
  const TankStatusChip({super.key, required this.status});

  final TankStatus status;

  @override
  Widget build(BuildContext context) {
    final (label, icon, color) = switch (status) {
      TankStatus.healthy => (
        'Healthy',
        Icons.check_circle_rounded,
        TankCtlColors.success,
      ),
      TankStatus.ok => ('OK', Icons.check_rounded, TankCtlColors.primary),
      TankStatus.highTemp => (
        'HIGH TEMP ⚠',
        Icons.thermostat_rounded,
        TankCtlColors.temperature,
      ),
      TankStatus.lowTemp => (
        'LOW TEMP ⚠',
        Icons.ac_unit_rounded,
        const Color(0xFF93C5FD),
      ),
      TankStatus.offline => (
        'Offline',
        Icons.cloud_off_rounded,
        Colors.white24,
      ),
      TankStatus.unknown => (
        'Unknown',
        Icons.help_outline_rounded,
        Colors.white24,
      ),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}

class TankWarningChip extends StatelessWidget {
  const TankWarningChip({super.key, required this.code});

  final String code;

  String get _label => switch (code) {
        'sensor_unavailable' => 'No Temp Sensor',
        _ => 'Warning',
      };

  @override
  Widget build(BuildContext context) {
    const color = Color(0xFFFFA726);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.sensors_off_rounded, size: 11, color: color),
          const SizedBox(width: 4),
          Text(
            _label,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}
