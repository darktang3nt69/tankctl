import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';
import 'package:tankctl_app/providers/device_provider.dart';
import 'package:tankctl_app/providers/light_provider.dart';
import 'package:tankctl_app/providers/telemetry_provider.dart';
import 'package:tankctl_app/widgets/status_indicator.dart';
import 'package:tankctl_app/widgets/temperature_mini_chart.dart';

// ── Helpers ───────────────────────────────────────────────────────────────────

DateTime? _parseIso(String? raw) {
  if (raw == null) return null;
  return DateTime.tryParse(raw)?.toLocal();
}

String _emojiFor(String deviceId) {
  const emojis = ['🐠', '🌿', '🪸', '🐡', '🦀', '🐙', '🦑', '🐬'];
  return emojis[deviceId.hashCode.abs() % emojis.length];
}

String _displayName(String id) => id
    .replaceAll(RegExp(r'[_\-]'), ' ')
    .split(' ')
    .map((w) => w.isEmpty ? '' : '${w[0].toUpperCase()}${w.substring(1)}')
    .join(' ');

String _formatAge(DateTime? lastSeen) {
  if (lastSeen == null) return 'No data';
  final diff = DateTime.now().difference(lastSeen);
  if (diff.inSeconds < 60) return '${diff.inSeconds}s ago';
  if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
  // For stale data, show actual date + time instead of "84h ago"
  final h = lastSeen.hour.toString().padLeft(2, '0');
  final m = lastSeen.minute.toString().padLeft(2, '0');
  const months = [
    'Jan',
    'Feb',
    'Mar',
    'Apr',
    'May',
    'Jun',
    'Jul',
    'Aug',
    'Sep',
    'Oct',
    'Nov',
    'Dec',
  ];
  return '${months[lastSeen.month - 1]} ${lastSeen.day}, $h:$m';
}

enum _TankStatus { healthy, ok, highTemp, lowTemp, offline, unknown }

_TankStatus _evaluate(double? temp, bool isOnline) {
  if (!isOnline) return _TankStatus.offline;
  if (temp == null) return _TankStatus.unknown;
  if (temp > 28.0) return _TankStatus.highTemp;
  if (temp < 18.0) return _TankStatus.lowTemp;
  if (temp > 26.5) return _TankStatus.ok;
  return _TankStatus.healthy;
}

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
    final shadowAsync = ref.watch(deviceShadowProvider(deviceId));
    // Rebuild every second so "Xs ago" ticks forward.
    ref.watch(secondTickProvider);
    final wsLastSeen = ref.watch(lastTelemetryTimeProvider(deviceId));
    final deviceAsync = ref.watch(singleDeviceProvider(deviceId));
    final deviceLastSeen = _parseIso(
      deviceAsync.valueOrNull?['last_seen'] as String?,
    );
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

    final status = _evaluate(latestTemp, isOnline);
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
                      _emojiFor(deviceId),
                      style: const TextStyle(fontSize: 22),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        _displayName(deviceId),
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
                              : '—',
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
                    _StatusChip(status: status),
                    const Spacer(),
                    const Icon(
                      Icons.access_time_rounded,
                      size: 12,
                      color: Colors.white24,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      _formatAge(lastSeen),
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

// ── Status chip ───────────────────────────────────────────────────────────────

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});
  final _TankStatus status;

  @override
  Widget build(BuildContext context) {
    final (label, icon, color) = switch (status) {
      _TankStatus.healthy => (
        'Healthy',
        Icons.check_circle_rounded,
        TankCtlColors.success,
      ),
      _TankStatus.ok => ('OK', Icons.check_rounded, TankCtlColors.primary),
      _TankStatus.highTemp => (
        'HIGH TEMP ⚠',
        Icons.thermostat_rounded,
        TankCtlColors.temperature,
      ),
      _TankStatus.lowTemp => (
        'LOW TEMP ⚠',
        Icons.ac_unit_rounded,
        const Color(0xFF93C5FD),
      ),
      _TankStatus.offline => (
        'Offline',
        Icons.cloud_off_rounded,
        Colors.white24,
      ),
      _TankStatus.unknown => (
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
