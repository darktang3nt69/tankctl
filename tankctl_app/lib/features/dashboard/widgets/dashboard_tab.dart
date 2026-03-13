import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:tankctl_app/core/api/api_constants.dart';
import 'package:tankctl_app/features/dashboard/providers/attention_dismissals_provider.dart';
import 'package:tankctl_app/features/dashboard/widgets/dashboard_attention_builder.dart';
import 'package:tankctl_app/features/dashboard/widgets/dashboard_list_controls.dart';
import 'package:tankctl_app/features/dashboard/widgets/dashboard_sorting.dart';
import 'package:tankctl_app/features/dashboard/widgets/needs_attention_strip.dart';
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

  SortMeta _buildSortMeta(Map<String, dynamic> device) {
    final deviceId = device['device_id'] as String;
    final isOnline = device['status'] == 'online';
    final warningCode = ref.watch(deviceWarningProvider(deviceId));
    final liveTemp = ref.watch(liveTelemetryProvider(deviceId)).valueOrNull;
    final history =
        ref.watch(temperatureHistoryProvider(deviceId)).valueOrNull ??
        const <double>[];
    final latestTemp = warningCode == 'sensor_unavailable'
        ? null
        : (liveTemp ?? (history.isNotEmpty ? history.last : null));
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

  @override
  Widget build(BuildContext context) {
    final devicesAsync = ref.watch(devicesListProvider);
    final dismissedKeysAsync = ref.watch(attentionDismissalsProvider);
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
          DashboardListControls(
            showOnlineOnly: _showOnlineOnly,
            onToggleOnlineOnly: (v) => setState(() => _showOnlineOnly = v),
            sortMode: _sortMode,
            onSortModeChanged: (mode) => setState(() => _sortMode = mode),
          ),
          const SizedBox(height: 12),
          devicesAsync.when(
            data: (devices) {
              final attentionIssues = buildAttentionIssues(ref, devices);
              final dismissedKeys =
                  dismissedKeysAsync.valueOrNull ?? const <String>{};
              final visibleAttentionIssues = attentionIssues
                  .where((issue) => !dismissedKeys.contains(issue.issueKey))
                  .toList();
              final filtered = _showOnlineOnly
                  ? devices.where((d) => d['status'] == 'online').toList()
                  : devices;
              final sorted = _sortDevices(filtered);
              return Column(
                children: [
                  if (visibleAttentionIssues.isNotEmpty) ...[
                    NeedsAttentionStrip(
                      issues: visibleAttentionIssues,
                      onTapIssue: (deviceId) => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => TankDetailScreen(deviceId: deviceId),
                        ),
                      ),
                      onDismissIssue: (issue) async {
                        try {
                          await ref
                              .read(attentionDismissalsProvider.notifier)
                              .dismissIssue(
                                deviceId: issue.deviceId,
                                warningCode: issue.issueTypeName,
                              );
                        } on DioException catch (e) {
                          if (!context.mounted) {
                            return;
                          }
                          final msg =
                              e.response?.data is Map &&
                                  (e.response?.data as Map)['detail'] is String
                              ? (e.response?.data as Map)['detail'] as String
                              : 'Could not dismiss issue';
                          ScaffoldMessenger.of(
                            context,
                          ).showSnackBar(SnackBar(content: Text(msg)));
                        } catch (_) {
                          if (!context.mounted) {
                            return;
                          }
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('Could not dismiss issue'),
                            ),
                          );
                        }
                      },
                    ),
                    const SizedBox(height: 12),
                  ] else ...[
                    const NoAttentionBanner(),
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
                    style: textTheme.bodyMedium?.copyWith(
                      color: Colors.white38,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    backendLabel,
                    style: textTheme.labelSmall?.copyWith(
                      color: Colors.white24,
                    ),
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
