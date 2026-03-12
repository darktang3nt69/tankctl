import 'package:flutter/material.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';
import 'package:tankctl_app/widgets/status_indicator.dart';
import 'package:tankctl_app/widgets/tank_card_chips.dart';
import 'package:tankctl_app/widgets/tank_card_helpers.dart';

class TankCardHeader extends StatelessWidget {
  const TankCardHeader({
    super.key,
    required this.deviceId,
    required this.isOnline,
  });

  final String deviceId;
  final bool isOnline;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Row(
      children: [
        Text(
          emojiForDevice(deviceId),
          style: const TextStyle(fontSize: 22),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            displayNameFromDeviceId(deviceId),
            style: textTheme.titleMedium?.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.w700,
            ),
            overflow: TextOverflow.ellipsis,
          ),
        ),
        const SizedBox(width: 8),
        StatusIndicator(isOnline: isOnline),
      ],
    );
  }
}

class TankCardMetricsRow extends StatelessWidget {
  const TankCardMetricsRow({
    super.key,
    required this.latestTemp,
    required this.tempHigh,
    required this.lightOn,
    required this.onToggleLight,
  });

  final double? latestTemp;
  final bool tempHigh;
  final bool lightOn;
  final ValueChanged<bool> onToggleLight;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Temp',
              style: textTheme.labelSmall?.copyWith(
                color: Colors.white38,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              latestTemp != null ? '${latestTemp!.toStringAsFixed(1)}°C' : '--',
              style: TextStyle(
                fontSize: 30,
                fontWeight: FontWeight.bold,
                color: tempHigh ? TankCtlColors.temperature : Colors.white,
                letterSpacing: -1,
                height: 1,
              ),
            ),
          ],
        ),
        const Spacer(),
        Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              'Light',
              style: textTheme.labelSmall?.copyWith(
                color: Colors.white38,
              ),
            ),
            const SizedBox(height: 2),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  lightOn ? 'ON' : 'OFF',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: lightOn ? TankCtlColors.warning : Colors.white38,
                  ),
                ),
                const SizedBox(width: 2),
                GestureDetector(
                  onTap: () {},
                  behavior: HitTestBehavior.opaque,
                  child: Transform.scale(
                    scale: 0.75,
                    alignment: Alignment.centerRight,
                    child: Switch(
                      value: lightOn,
                      onChanged: onToggleLight,
                      activeThumbColor: TankCtlColors.warning,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ],
    );
  }
}

class TankCardFooter extends StatelessWidget {
  const TankCardFooter({
    super.key,
    required this.status,
    required this.warningCode,
    required this.lastSeen,
  });

  final TankStatus status;
  final String? warningCode;
  final DateTime? lastSeen;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Row(
      children: [
        TankStatusChip(status: status),
        if (warningCode != null) ...[
          const SizedBox(width: 6),
          TankWarningChip(code: warningCode!),
        ],
        const Spacer(),
        const Icon(
          Icons.access_time_rounded,
          size: 12,
          color: Colors.white24,
        ),
        const SizedBox(width: 4),
        Text(
          formatAgeFromLastSeen(lastSeen),
          style: textTheme.labelSmall?.copyWith(
            color: Colors.white38,
          ),
        ),
      ],
    );
  }
}
