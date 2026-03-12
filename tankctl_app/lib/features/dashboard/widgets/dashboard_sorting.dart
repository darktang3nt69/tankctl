import 'package:tankctl_app/features/dashboard/widgets/needs_attention_strip.dart';

enum DashboardSortMode {
  alphabetical,
  mostRecentlyUpdated,
  hottest,
  warningFirst,
  offlineFirst,
}

class SortMeta {
  const SortMeta({
    required this.online,
    required this.warningCode,
    required this.latestTemp,
    required this.lastSeen,
  });

  final bool online;
  final String? warningCode;
  final double? latestTemp;
  final DateTime? lastSeen;
}

String sortLabel(DashboardSortMode mode) => switch (mode) {
      DashboardSortMode.alphabetical => 'Alphabetical',
      DashboardSortMode.mostRecentlyUpdated => 'Most Recent',
      DashboardSortMode.hottest => 'Hottest',
      DashboardSortMode.warningFirst => 'Warning First',
      DashboardSortMode.offlineFirst => 'Offline First',
    };

String deviceLabel(String deviceId) {
  final normalized = deviceId.replaceAll(RegExp(r'[_-]+'), ' ').trim();
  if (normalized.isEmpty) {
    return deviceId;
  }
  return normalized
      .split(RegExp(r'\s+'))
      .map(
        (word) => word.isEmpty ? word : '${word[0].toUpperCase()}${word.substring(1)}',
      )
      .join(' ');
}

DateTime? parseIsoToLocal(String? raw) {
  if (raw == null) {
    return null;
  }
  return DateTime.tryParse(raw)?.toLocal();
}

int compareNullableDesc<T extends Comparable<T>>(T? a, T? b) {
  if (a == null && b == null) {
    return 0;
  }
  if (a == null) {
    return 1;
  }
  if (b == null) {
    return -1;
  }
  return b.compareTo(a);
}

int issuePriority(AttentionIssueType type) => switch (type) {
      AttentionIssueType.offline => 0,
      AttentionIssueType.noTempSensor => 1,
      AttentionIssueType.highTemp => 2,
      AttentionIssueType.lowTemp => 3,
    };

AttentionIssueType? issueTypeFromMeta(
  SortMeta meta, {
  required double highTempThreshold,
  required double lowTempThreshold,
}) {
  if (!meta.online) {
    return AttentionIssueType.offline;
  }
  if (meta.warningCode == 'sensor_unavailable') {
    return AttentionIssueType.noTempSensor;
  }
  final temp = meta.latestTemp;
  if (temp != null && temp > highTempThreshold) {
    return AttentionIssueType.highTemp;
  }
  if (temp != null && temp < lowTempThreshold) {
    return AttentionIssueType.lowTemp;
  }
  return null;
}

List<Map<String, dynamic>> sortDevices({
  required List<Map<String, dynamic>> devices,
  required DashboardSortMode sortMode,
  required Map<String, SortMeta> metaById,
}) {
  final sorted = [...devices];

  int compareDeviceId(Map<String, dynamic> a, Map<String, dynamic> b) {
    final aId = a['device_id'] as String;
    final bId = b['device_id'] as String;
    return aId.compareTo(bId);
  }

  sorted.sort((a, b) {
    final aId = a['device_id'] as String;
    final bId = b['device_id'] as String;
    final aMeta = metaById[aId]!;
    final bMeta = metaById[bId]!;

    switch (sortMode) {
      case DashboardSortMode.alphabetical:
        return compareDeviceId(a, b);

      case DashboardSortMode.mostRecentlyUpdated:
        final byRecent = compareNullableDesc(aMeta.lastSeen, bMeta.lastSeen);
        if (byRecent != 0) {
          return byRecent;
        }
        return compareDeviceId(a, b);

      case DashboardSortMode.hottest:
        final byTemp = compareNullableDesc(aMeta.latestTemp, bMeta.latestTemp);
        if (byTemp != 0) {
          return byTemp;
        }
        return compareDeviceId(a, b);

      case DashboardSortMode.warningFirst:
        final aIssue = issueTypeFromMeta(
          aMeta,
          highTempThreshold: 28.0,
          lowTempThreshold: 18.0,
        );
        final bIssue = issueTypeFromMeta(
          bMeta,
          highTempThreshold: 28.0,
          lowTempThreshold: 18.0,
        );
        final aHasIssue = aIssue != null;
        final bHasIssue = bIssue != null;

        if (aHasIssue != bHasIssue) {
          return aHasIssue ? -1 : 1;
        }

        if (aIssue != null && bIssue != null) {
          final bySeverity = issuePriority(aIssue).compareTo(issuePriority(bIssue));
          if (bySeverity != 0) {
            return bySeverity;
          }
        }

        final byRecent = compareNullableDesc(aMeta.lastSeen, bMeta.lastSeen);
        if (byRecent != 0) {
          return byRecent;
        }
        return compareDeviceId(a, b);

      case DashboardSortMode.offlineFirst:
        if (aMeta.online != bMeta.online) {
          return aMeta.online ? 1 : -1;
        }

        final byRecent = compareNullableDesc(aMeta.lastSeen, bMeta.lastSeen);
        if (byRecent != 0) {
          return byRecent;
        }
        return compareDeviceId(a, b);
    }
  });

  return sorted;
}
