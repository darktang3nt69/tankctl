import 'package:flutter/material.dart';
import 'package:tankctl_app/utils/app_icons.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';
import 'package:tankctl_app/widgets/tank_card_helpers.dart';


class TankStatusChip extends StatelessWidget {
  final TankStatus status;
  final String? deviceWarning;

  const TankStatusChip({Key? key, required this.status, this.deviceWarning}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    String label;
    IconData icon;
    Color color;

    switch (status) {
      case TankStatus.healthy:
        label = 'Healthy';
        icon = AppIcons.checkCircle;
        color = TankCtlColors.success;
        break;
      case TankStatus.ok:
        label = 'OK';
        icon = AppIcons.check;
        color = TankCtlColors.primary;
        break;
      case TankStatus.highTemp:
        label = 'HIGH TEMP ⚠';
        icon = AppIcons.thermostat;
        color = TankCtlColors.temperature;
        break;
      case TankStatus.lowTemp:
        label = 'LOW TEMP ⚠';
        icon = AppIcons.acUnit;
        color = const Color(0xFF93C5FD);
        break;
      case TankStatus.offline:
        label = 'Offline';
        icon = AppIcons.cloudOff;
        color = Colors.white24;
        break;
      case TankStatus.unknown:
        if (deviceWarning == 'sensor_unavailable') {
          label = 'No Temp Sensor';
          icon = AppIcons.sensorsOff;
          color = Colors.white24;
        } else {
          label = 'No Data';
          icon = AppIcons.help;
          color = Colors.white24;
        }
        break;
    }

    return Chip(
      label: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 6),
          Text(label, style: TextStyle(color: color)),
        ],
      ),
      backgroundColor: Colors.transparent,
      shape: StadiumBorder(side: BorderSide(color: color.withOpacity(0.3))),
    );
  }
}

class TankWarningChip extends StatelessWidget {
  const TankWarningChip({
    super.key,
    required this.code,
    this.onAcknowledge,
  });

  final String code;
  final VoidCallback? onAcknowledge;

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
          const Icon(AppIcons.sensorsOff, size: 11, color: color),
          const SizedBox(width: 4),
          Text(
            _label,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
          if (onAcknowledge != null) ...[
            const SizedBox(width: 4),
            InkWell(
              borderRadius: BorderRadius.circular(10),
              onTap: onAcknowledge,
              child: const Padding(
                padding: EdgeInsets.all(1),
                child: Icon(
                  AppIcons.close,
                  size: 12,
                  color: color,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class FirmwareVersionChip extends StatelessWidget {
  const FirmwareVersionChip({
    super.key,
    required this.version,
  });

  final String version;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white24),
      ),
      child: Text(
        version.startsWith('v') ? version : 'v$version',
        style: const TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w600,
          color: Colors.white70,
          fontFamily: 'monospace',
        ),
      ),
    );
  }
}
