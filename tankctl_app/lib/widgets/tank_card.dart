import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';
import 'package:tankctl_app/features/dashboard/providers/attention_dismissals_provider.dart';
import 'package:tankctl_app/providers/device_provider.dart';
import 'package:tankctl_app/providers/telemetry_provider.dart';
import 'package:tankctl_app/services/device_service.dart';
import 'package:tankctl_app/widgets/tank_card_helpers.dart';
import 'package:tankctl_app/widgets/tank_card_sections.dart';

// ── TankCard ──────────────────────────────────────────────────────────────────

/// Dashboard card showing summary information for a single tank device.
class TankCard extends ConsumerWidget {
  const TankCard({
    super.key,
    required this.deviceId,
    required this.isOnline,
    required this.onTap,
  });

  final String deviceId;
  final bool isOnline;
  final VoidCallback onTap;

  Future<void> _confirmAndReboot(BuildContext context, WidgetRef ref) async {
    final shouldReboot = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Reboot device?'),
        content: Text('Reboot $deviceId now?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Reboot'),
          ),
        ],
      ),
    );

    if (shouldReboot == true) {
      await ref.read(deviceServiceProvider).rebootDevice(deviceId);
    }
  }

  Future<void> _refreshTank(WidgetRef ref) async {
    await ref.read(deviceServiceProvider).requestStatus(deviceId);
    ref.invalidate(temperatureHistoryProvider(deviceId));
    ref.invalidate(deviceShadowProvider(deviceId));
    ref.invalidate(devicesListProvider);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final liveTemp = ref.watch(liveTelemetryProvider(deviceId)).valueOrNull;
    final deviceWarning = ref.watch(deviceWarningProvider(deviceId));
    final acknowledgedWarnings =
        ref.watch(attentionDismissalsProvider).valueOrNull ?? const <String>{};
    // Rebuild every second so "Xs ago" ticks forward.
    ref.watch(secondTickProvider);
    final wsLastSeen = ref.watch(lastTelemetryTimeProvider(deviceId));
    final devicesAsync = ref.watch(devicesListProvider);
    final deviceData = devicesAsync.valueOrNull?.firstWhere(
      (d) => d['device_id'] == deviceId,
      orElse: () => const <String, dynamic>{},
    );
    final deviceLastSeen = parseIsoToLocal(deviceData?['last_seen'] as String?);
    final lastSeen = wsLastSeen ?? deviceLastSeen;

    final history = ref.watch(temperatureHistoryProvider(deviceId)).valueOrNull ?? const [];

    // Light state from device shadow (reported.light)
    final shadowAsync = ref.watch(deviceShadowProvider(deviceId));
    final shadowReported =
        shadowAsync.valueOrNull?['reported'] as Map<String, dynamic>?;
    final lightState = shadowReported?['light'] as String?;
    final lightOn = lightState == null ? null : lightState == 'on';

    // When the device reports a missing sensor, do not surface stale
    // historical values as "current" temperature.
    final latestTemp = deviceWarning == 'sensor_unavailable'
        ? null
        : (liveTemp ?? (history.isNotEmpty ? history.last : null));

    final status = evaluateTankStatus(latestTemp, isOnline);
    final thresholdHigh = (deviceData?['temp_threshold_high'] as num?)
        ?.toDouble();
    final effectiveHigh = thresholdHigh ?? 28.0;
    final tempHigh = latestTemp != null && latestTemp > effectiveHigh;
    final rssi = (deviceData?['rssi'] as num?)?.toInt();
    final firmwareVersion = deviceData?['firmware_version'] as String?;
    final warningKey = deviceWarning == null
        ? null
        : '${deviceId}_$deviceWarning';
    final effectiveWarning =
        (warningKey != null && acknowledgedWarnings.contains(warningKey))
        ? null
        : deviceWarning;

    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: Material(
        color: TankCtlColors.card,
        elevation: 4,
        shadowColor: Colors.black45,
        child: InkWell(
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TankCardHeader(
                  deviceId: deviceId,
                  isOnline: isOnline,
                  rssi: rssi,
                  firmwareVersion: firmwareVersion,
                  onRefresh: () => _refreshTank(ref),
                  onReboot: () => _confirmAndReboot(context, ref),
                ),

                const SizedBox(height: 8),
                const Divider(color: Colors.white10, height: 1),
                const SizedBox(height: 8),

                TankCardMetricsRow(
                  latestTemp: latestTemp,
                  tempHigh: tempHigh,
                  lightOn: lightOn,
                ),

                const SizedBox(height: 8),

                TankCardFooter(
                  status: status,
                  warningCode: effectiveWarning,
                  lastSeen: lastSeen,
                  onAcknowledgeWarning: effectiveWarning == null
                      ? null
                      : () async {
                          await ref
                              .read(deviceServiceProvider)
                              .acknowledgeWarning(deviceId, effectiveWarning);
                          ref.invalidate(attentionDismissalsProvider);
                          ref.invalidate(deviceWarningProvider(deviceId));
                        },
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
