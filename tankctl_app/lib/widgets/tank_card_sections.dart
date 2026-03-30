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
    this.lightOn,
  });

  final double? latestTemp;
  final bool tempHigh;
  final bool? lightOn;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Temperature block
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'TEMP',
                style: textTheme.labelSmall?.copyWith(
                  color: Colors.white38,
                  letterSpacing: 0.8,
                  fontSize: 10,
                ),
              ),
              const SizedBox(height: 1),
              Text(
                latestTemp != null
                    ? '${latestTemp!.toStringAsFixed(1)}°C'
                    : '--',
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.bold,
                  color:
                      tempHigh ? TankCtlColors.temperature : Colors.white,
                  letterSpacing: -0.5,
                  height: 1,
                ),
              ),
            ],
          ),
        ),
        // Light status chip
        if (lightOn != null) _LightStatusChip(lightOn: lightOn!),
      ],
    );
  }
}

class _LightStatusChip extends StatelessWidget {
  const _LightStatusChip({required this.lightOn});

  final bool lightOn;

  static const _amber = Color(0xFFFFD54F);

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: lightOn
            ? _amber.withValues(alpha: 0.14)
            : Colors.white.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: lightOn
              ? _amber.withValues(alpha: 0.55)
              : Colors.white.withValues(alpha: 0.14),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            lightOn ? Icons.light_mode_rounded : Icons.light_mode_outlined,
            size: 13,
            color: lightOn ? _amber : Colors.white38,
          ),
          const SizedBox(width: 4),
          Text(
            lightOn ? 'On' : 'Off',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: lightOn ? _amber : Colors.white38,
            ),
          ),
        ],
      ),
    );
  }
}


class TankCardFooter extends StatelessWidget {
  final TankStatus status;
  final String? warningCode;
  final DateTime? lastSeen;
  final VoidCallback? onAcknowledgeWarning;

  const TankCardFooter({
    super.key,
    required this.status,
    required this.warningCode,
    required this.lastSeen,
    required this.onAcknowledgeWarning,
  });

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Row(
      children: [
        TankStatusChip(
          status: status,
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
