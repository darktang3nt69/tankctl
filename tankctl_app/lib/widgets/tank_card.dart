import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';
import 'package:tankctl_app/features/dashboard/providers/attention_dismissals_provider.dart';
import 'package:tankctl_app/providers/device_provider.dart';
import 'package:tankctl_app/providers/light_provider.dart';
import 'package:tankctl_app/providers/telemetry_provider.dart';
import 'package:tankctl_app/services/device_service.dart';
import 'package:tankctl_app/widgets/tank_card_helpers.dart';
import 'package:tankctl_app/widgets/tank_card_sections.dart';
import 'package:tankctl_app/widgets/temperature_mini_chart.dart';

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
    final historyAsync = ref.watch(temperatureHistoryProvider(deviceId));
    // Watch the full AsyncValue so we can distinguish cold-start (AsyncLoading)
    final liveTemp = ref.watch(liveTelemetryProvider(deviceId)).valueOrNull;
    final deviceWarning = ref.watch(deviceWarningProvider(deviceId));
    final shadowAsync = ref.watch(deviceShadowProvider(deviceId));
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

    final history = historyAsync.valueOrNull ?? const [];

    // wsLastSeen is set by main.dart on every telemetry_received WS event
    // (including events where temperature normalised away to null).  It is a
    // StateProvider so it survives WS reconnections, unlike the StreamProvider
    // which resets to AsyncLoading on reconnect and would otherwise cause a
    // brief fallback to the stale history value.
    final hasReceivedLiveTelemetry = wsLastSeen != null;
    final latestTemp = hasReceivedLiveTelemetry
        ? liveTemp
        : (history.isNotEmpty ? history.last : null);

    final reported = shadowAsync.valueOrNull?['reported'] as Map?;
    final lightFamilyAsync = ref.watch(lightStateFamilyProvider(deviceId));
    final lightOn =
        lightFamilyAsync.valueOrNull ?? (reported?['light'] == 'on');

    final status = evaluateTankStatus(latestTemp, isOnline);
    final thresholdHigh = (deviceData?['temp_threshold_high'] as num?)?.toDouble();
    final thresholdLow = (deviceData?['temp_threshold_low'] as num?)?.toDouble();
    final effectiveHigh = thresholdHigh ?? 28.0;
    final tempHigh = latestTemp != null && latestTemp > effectiveHigh;
    final rssi = (deviceData?['rssi'] as num?)?.toInt();
    final firmwareVersion = deviceData?['firmware_version'] as String?;

    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: Material(
        color: TankCtlColors.card,
        elevation: 4,
        shadowColor: Colors.black45,
        child: InkWell(
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TankCardHeader(
                  deviceId: deviceId,
                  isOnline: isOnline,
                  rssi: rssi,
                  onRefresh: () => _refreshTank(ref),
                  onReboot: () => _confirmAndReboot(context, ref),
                ),

                const SizedBox(height: 12),
                const Divider(color: Colors.white10, height: 1),
                const SizedBox(height: 14),

                TankCardMetricsRow(
                  latestTemp: latestTemp,
                  tempHigh: tempHigh,
                  lightOn: lightOn,
                  onToggleLight: (v) => ref
                      .read(lightStateFamilyProvider(deviceId).notifier)
                      .toggle(v),
                ),

                // ── Sparkline ─────────────────────────────────────────
                if (history.length >= 2) ...[
                  const SizedBox(height: 12),
                  TemperatureMiniChart(
                    data: history,
                    height: 40,
                    color: isOnline ? TankCtlColors.primary : Colors.white12,
                    thresholdHigh: thresholdHigh,
                    thresholdLow: thresholdLow,
                  ),
                ],

                const SizedBox(height: 12),

                TankCardFooter(
                  status: status,
                  warningCode: deviceWarning,
                  lastSeen: lastSeen,
                  firmwareVersion: firmwareVersion,
                  onAcknowledgeWarning: deviceWarning == null
                      ? null
                      : () async {
                          await ref.read(deviceServiceProvider).acknowledgeWarning(
                                deviceId,
                                deviceWarning,
                              );
                          ref.invalidate(attentionDismissalsProvider);
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
