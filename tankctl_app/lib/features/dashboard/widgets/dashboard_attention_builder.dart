import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/features/dashboard/widgets/dashboard_sorting.dart';
import 'package:tankctl_app/features/dashboard/widgets/needs_attention_strip.dart';
import 'package:tankctl_app/providers/telemetry_provider.dart';

const highTempThreshold = 28.0;
const lowTempThreshold = 18.0;

List<AttentionIssue> buildAttentionIssues(
  WidgetRef ref,
  List<Map<String, dynamic>> devices,
) {
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

    if (latestTemp != null && latestTemp > highTempThreshold) {
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

    if (latestTemp != null && latestTemp < lowTempThreshold) {
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
