import 'package:flutter/material.dart';
import 'package:tankctl_app/utils/app_icons.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';
import 'package:tankctl_app/widgets/tank_card_chips.dart';
import 'package:tankctl_app/widgets/tank_card_helpers.dart';

class TankCardHeader extends StatelessWidget {
  const TankCardHeader({
    super.key,
    required this.deviceId,
    required this.isOnline,
    required this.rssi,
    this.firmwareVersion,
    required this.onRefresh,
    required this.onReboot,
  });

  final String deviceId;
  final bool isOnline;
  final int? rssi;
  final String? firmwareVersion;
  final VoidCallback onRefresh;
  final VoidCallback onReboot;

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
          child: Row(
            children: [
              Flexible(
                child: Text(
                  displayNameFromDeviceId(deviceId),
                  style: textTheme.titleMedium?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (firmwareVersion != null && firmwareVersion!.isNotEmpty) ...[
                const SizedBox(width: 4),
                Transform.translate(
                  offset: const Offset(0, -5),
                  child: Text(
                    firmwareVersion!.startsWith('v')
                        ? firmwareVersion!
                        : 'v$firmwareVersion',
                    style: textTheme.labelSmall?.copyWith(
                      color: Colors.white54,
                      fontWeight: FontWeight.w600,
                      fontSize: 10,
                      letterSpacing: 0.2,
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
        const SizedBox(width: 8),
        _RssiStatusIcon(isOnline: isOnline, rssi: rssi),
        IconButton(
          onPressed: onRefresh,
          icon: const Icon(AppIcons.refresh, size: 18),
          color: Colors.white70,
          tooltip: 'Refresh this tank',
          splashRadius: 18,
        ),
        PopupMenuButton<String>(
          icon: const Icon(AppIcons.moreHoriz, color: Colors.white70, size: 20),
          splashRadius: 18,
          onSelected: (value) {
            if (value == 'reboot') {
              onReboot();
            }
          },
          itemBuilder: (_) => const [
            PopupMenuItem<String>(
              value: 'reboot',
              child: Text('Reboot device'),
            ),
          ],
        ),
      ],
    );
  }
}

class _RssiStatusIcon extends StatelessWidget {
  const _RssiStatusIcon({required this.isOnline, required this.rssi});

  final bool isOnline;
  final int? rssi;

  @override
  Widget build(BuildContext context) {
    if (!isOnline) {
      return const Icon(
        AppIcons.cloudOff,
        size: 18,
        color: Colors.white38,
      );
    }

    // Show a clear green wifi symbol when the device is online
    // (replace the small/ambiguous dot with a WiFi icon).
    return Icon(AppIcons.wifiStrong, size: 18, color: TankCtlColors.success);
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
  final TankStatus status;
  final String? warningCode;
  final DateTime? lastSeen;
  final VoidCallback? onAcknowledgeWarning;
  final String? deviceWarning;

  const TankCardFooter({
    super.key,
    required this.status,
    required this.warningCode,
    required this.lastSeen,
    required this.onAcknowledgeWarning,
    this.deviceWarning,
  });

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Row(
      children: [
        TankStatusChip(
          status: status,
          deviceWarning: deviceWarning,
        ),
        if (warningCode != null) ...[
          const SizedBox(width: 6),
          TankWarningChip(
            code: warningCode!,
            onAcknowledge: onAcknowledgeWarning,
          ),
        ],
        const Spacer(),
        const Icon(
          AppIcons.time,
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
