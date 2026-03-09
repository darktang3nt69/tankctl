import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';
import 'package:tankctl_app/providers/device_provider.dart';
import 'package:tankctl_app/providers/telemetry_provider.dart';
import 'package:tankctl_app/widgets/status_indicator.dart';
import 'package:tankctl_app/widgets/temperature_mini_chart.dart';

/// Dashboard card showing summary information for a single tank device.
/// Tapping the card navigates to the detail screen via [onTap].
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
    final shadowAsync = ref.watch(deviceShadowProvider(deviceId));
    final textTheme = Theme.of(context).textTheme;

    final history = historyAsync.valueOrNull ?? const [];
    final latestTemp = history.isNotEmpty ? history.last : null;
    final reported = shadowAsync.valueOrNull?['reported'] as Map?;
    final lightOn = reported?['light'] == 'on';

    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: Material(
        color: TankCtlColors.card,
        shadowColor: Colors.black54,
        elevation: 4,
        child: InkWell(
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Header ──────────────────────────────────────────────
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      deviceId,
                      style: textTheme.titleMedium?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    StatusIndicator(isOnline: isOnline),
                  ],
                ),
                const SizedBox(height: 20),

                // ── Temperature ──────────────────────────────────────────
                Center(
                  child: Column(
                    children: [
                      historyAsync.when(
                        data: (_) => Text(
                          latestTemp != null
                              ? '${latestTemp.toStringAsFixed(1)}°C'
                              : '—',
                          style: const TextStyle(
                            fontSize: 52,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                            height: 1,
                            letterSpacing: -2,
                          ),
                        ),
                        loading: () => Text(
                          '…',
                          style: textTheme.displaySmall?.copyWith(
                            color: Colors.white38,
                          ),
                        ),
                        error: (e, _) => Text(
                          '—',
                          style: textTheme.displaySmall?.copyWith(
                            color: Colors.white24,
                          ),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Temperature',
                        style: textTheme.labelSmall?.copyWith(
                          color: Colors.white38,
                          letterSpacing: 0.8,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // ── Sparkline ────────────────────────────────────────────
                TemperatureMiniChart(
                  data: history,
                  height: 56,
                  color: isOnline
                      ? TankCtlColors.primary
                      : Colors.white24,
                ),
                const SizedBox(height: 16),

                // ── Footer ───────────────────────────────────────────────
                Row(
                  children: [
                    Icon(
                      lightOn
                          ? Icons.lightbulb_rounded
                          : Icons.lightbulb_outline_rounded,
                      size: 16,
                      color: lightOn
                          ? TankCtlColors.warning
                          : Colors.white24,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      lightOn ? 'Light ON' : 'Light OFF',
                      style: TextStyle(
                        color: lightOn ? TankCtlColors.warning : Colors.white24,
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const Spacer(),
                    const Icon(
                      Icons.chevron_right_rounded,
                      color: Colors.white24,
                      size: 20,
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
