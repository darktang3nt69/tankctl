import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/api/api_constants.dart';
import 'package:tankctl_app/features/dashboard/widgets/needs_attention_strip.dart';
import 'package:tankctl_app/features/dashboard/widgets/dashboard_sorting.dart';
import 'package:tankctl_app/features/tank_detail/tank_detail_screen.dart';
import 'package:tankctl_app/providers/app_settings_provider.dart';
import 'package:tankctl_app/providers/device_provider.dart';
import 'package:tankctl_app/providers/telemetry_provider.dart';
import 'package:tankctl_app/widgets/tank_card.dart';
import 'package:tankctl_app/widgets/tank_overview_card.dart';

class DashboardTab extends ConsumerStatefulWidget {
  const DashboardTab({super.key, required this.onRefresh});

  final VoidCallback onRefresh;

  @override
  ConsumerState<DashboardTab> createState() => _DashboardTabState();
}

class _DashboardTabState extends ConsumerState<DashboardTab> {
  bool _showOnlineOnly = false;
  DashboardSortMode _sortMode = DashboardSortMode.alphabetical;

  static const _highTempThreshold = 28.0;
  static const _lowTempThreshold = 18.0;

  SortMeta _buildSortMeta(Map<String, dynamic> device) {
    final deviceId = device['device_id'] as String;
    final isOnline = device['status'] == 'online';
    final warningCode = ref.watch(deviceWarningProvider(deviceId));
    final liveTemp = ref.watch(liveTelemetryProvider(deviceId)).valueOrNull;
    final history =
        ref.watch(temperatureHistoryProvider(deviceId)).valueOrNull ??
        const <double>[];
    final latestTemp = liveTemp ?? (history.isNotEmpty ? history.last : null);
    final wsLastSeen = ref.watch(lastTelemetryTimeProvider(deviceId));
    final apiLastSeen = parseIsoToLocal(device['last_seen'] as String?);

    return SortMeta(
      online: isOnline,
      warningCode: warningCode,
      latestTemp: latestTemp,
      lastSeen: wsLastSeen ?? apiLastSeen,
    );
  }

  List<Map<String, dynamic>> _sortDevices(List<Map<String, dynamic>> devices) {
    final metaById = <String, SortMeta>{
      for (final device in devices)
        device['device_id'] as String: _buildSortMeta(device),
    };
    return sortDevices(
      devices: devices,
      sortMode: _sortMode,
      metaById: metaById,
    );
  }

  List<AttentionIssue> _buildAttentionIssues(List<Map<String, dynamic>> devices) {
    final issues = <AttentionIssue>[];

    for (final device in devices) {
      final deviceId = device['device_id'] as String;
      final isOnline = device['status'] == 'online';
      final label = deviceLabel(deviceId);

      if (!isOnline) {
        issues.add(
          AttentionIssue(
            deviceId: deviceId,
            deviceLabel: label,
            type: AttentionIssueType.offline,
          ),
        );
        continue;
      }

      final warningCode = ref.watch(deviceWarningProvider(deviceId));
      if (warningCode == 'sensor_unavailable') {
        issues.add(
          AttentionIssue(
            deviceId: deviceId,
            deviceLabel: label,
            type: AttentionIssueType.noTempSensor,
          ),
        );
        continue;
      }

      final liveTemp = ref.watch(liveTelemetryProvider(deviceId)).valueOrNull;
      final history =
          ref.watch(temperatureHistoryProvider(deviceId)).valueOrNull ??
          const <double>[];
      final latestTemp = liveTemp ?? (history.isNotEmpty ? history.last : null);

      if (latestTemp != null && latestTemp > _highTempThreshold) {
        issues.add(
          AttentionIssue(
            deviceId: deviceId,
            deviceLabel: label,
            type: AttentionIssueType.highTemp,
            temperature: latestTemp,
          ),
        );
        continue;
      }

      if (latestTemp != null && latestTemp < _lowTempThreshold) {
        issues.add(
          AttentionIssue(
            deviceId: deviceId,
            deviceLabel: label,
            type: AttentionIssueType.lowTemp,
            temperature: latestTemp,
          ),
        );
      }
    }

    issues.sort((a, b) {
      final bySeverity = issuePriority(a.type).compareTo(issuePriority(b.type));
      if (bySeverity != 0) {
        return bySeverity;
      }
      return a.deviceLabel.compareTo(b.deviceLabel);
    });

    return issues;
  }

  @override
  Widget build(BuildContext context) {
    final devicesAsync = ref.watch(devicesListProvider);
    final backendBaseUrl =
        ref.watch(serverBaseUrlProvider).valueOrNull ?? ApiConstants.baseUrl;
    final backendLabel = Uri.tryParse(backendBaseUrl)?.host.isNotEmpty == true
        ? '${Uri.parse(backendBaseUrl).host}${Uri.parse(backendBaseUrl).hasPort ? ':${Uri.parse(backendBaseUrl).port}' : ''}'
        : backendBaseUrl;
    final textTheme = Theme.of(context).textTheme;

    return RefreshIndicator(
      onRefresh: () async => widget.onRefresh(),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          const TankOverviewCard(),
          const SizedBox(height: 24),
          Row(
            children: [
              Text(
                'MY TANKS',
                style: textTheme.labelSmall?.copyWith(
                  color: Colors.white38,
                  letterSpacing: 1.4,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const Spacer(),
              FilterChip(
                label: const Text('Online only'),
                selected: _showOnlineOnly,
                onSelected: (v) => setState(() => _showOnlineOnly = v),
                visualDensity: VisualDensity.compact,
              ),
              const SizedBox(width: 8),
              PopupMenuButton<DashboardSortMode>(
                tooltip: 'Sort tanks',
                onSelected: (mode) => setState(() => _sortMode = mode),
                itemBuilder: (context) => DashboardSortMode.values
                    .map(
                      (mode) => PopupMenuItem<DashboardSortMode>(
                        value: mode,
                        child: Row(
                          children: [
                            if (mode == _sortMode)
                              const Icon(Icons.check_rounded, size: 16)
                            else
                              const SizedBox(width: 16),
                            const SizedBox(width: 8),
                            Text(sortLabel(mode)),
                          ],
                        ),
                      ),
                    )
                    .toList(),
                child: Chip(
                  visualDensity: VisualDensity.compact,
                  avatar: const Icon(Icons.sort_rounded, size: 16),
                  label: Text(sortLabel(_sortMode)),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          devicesAsync.when(
            data: (devices) {
              final attentionIssues = _buildAttentionIssues(devices);
              final filtered = _showOnlineOnly
                  ? devices.where((d) => d['status'] == 'online').toList()
                  : devices;
              final sorted = _sortDevices(filtered);
              return Column(
                children: [
                  if (attentionIssues.isNotEmpty) ...[
                    NeedsAttentionStrip(
                      issues: attentionIssues,
                      onTapIssue: (deviceId) => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => TankDetailScreen(deviceId: deviceId),
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                  ],
                  for (final device in sorted) ...[
                    TankCard(
                      deviceId: device['device_id'] as String,
                      isOnline: device['status'] == 'online',
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => TankDetailScreen(
                            deviceId: device['device_id'] as String,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                  ],
                ],
              );
            },
            loading: () => const Padding(
              padding: EdgeInsets.symmetric(vertical: 48),
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (e, _) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 48),
              child: Column(
                children: [
                  const Icon(
                    Icons.wifi_off_rounded,
                    size: 56,
                    color: Colors.white12,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Could not reach backend',
                    style: textTheme.bodyMedium?.copyWith(color: Colors.white38),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    backendLabel,
                    style: textTheme.labelSmall?.copyWith(color: Colors.white24),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
