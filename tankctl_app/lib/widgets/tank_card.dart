import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';
import 'package:tankctl_app/providers/device_provider.dart';
import 'package:tankctl_app/providers/light_provider.dart';
import 'package:tankctl_app/providers/telemetry_provider.dart';
import 'package:tankctl_app/widgets/status_indicator.dart';
import 'package:tankctl_app/widgets/tank_card_chips.dart';
import 'package:tankctl_app/widgets/tank_card_helpers.dart';
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

    final textTheme = Theme.of(context).textTheme;
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
    final tempHigh = latestTemp != null && latestTemp > 28.0;

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
                // ── Header: emoji + name + online dot ─────────────────
                Row(
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
                ),

                const SizedBox(height: 12),
                const Divider(color: Colors.white10, height: 1),
                const SizedBox(height: 14),

                // ── Temp (left) + Light toggle (right) ────────────────
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    // Temperature
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
                          latestTemp != null
                              ? '${latestTemp.toStringAsFixed(1)}°C'
                              : '--',
                          style: TextStyle(
                            fontSize: 30,
                            fontWeight: FontWeight.bold,
                            color: tempHigh
                                ? TankCtlColors.temperature
                                : Colors.white,
                            letterSpacing: -1,
                            height: 1,
                          ),
                        ),
                      ],
                    ),
                    const Spacer(),
                    // Light
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
                                color: lightOn
                                    ? TankCtlColors.warning
                                    : Colors.white38,
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
                                  onChanged: (v) => ref
                                      .read(
                                        lightStateFamilyProvider(
                                          deviceId,
                                        ).notifier,
                                      )
                                      .toggle(v),
                                  activeThumbColor: TankCtlColors.warning,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ],
                ),

                // ── Sparkline ─────────────────────────────────────────
                if (history.length >= 2) ...[
                  const SizedBox(height: 12),
                  TemperatureMiniChart(
                    data: history,
                    height: 40,
                    color: isOnline ? TankCtlColors.primary : Colors.white12,
                  ),
                ],

                const SizedBox(height: 12),

                // ── Status chip + last update ─────────────────────────
                Row(
                  children: [
                    TankStatusChip(status: status),
                    if (deviceWarning != null) ...[
                      const SizedBox(width: 6),
                      TankWarningChip(code: deviceWarning),
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
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
