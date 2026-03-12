import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/api/api_client.dart';

class AttentionDismissalsNotifier extends AsyncNotifier<Set<String>> {
  @override
  Future<Set<String>> build() async {
    return _fetchDismissedIssueKeys();
  }

  Future<Set<String>> _fetchDismissedIssueKeys() async {
    final dio = ref.read(dioProvider);
    final response = await dio.get(
      '/events',
      queryParameters: {
        'event_type': 'attention_dismissed',
        'limit': 1000,
      },
    );

    final rows = response.data;
    if (rows is! List) {
      return <String>{};
    }

    final keys = <String>{};
    for (final row in rows) {
      if (row is! Map) {
        continue;
      }
      final metadata = row['metadata'];
      if (metadata is! Map) {
        continue;
      }
      final rawKey = metadata['issue_key'];
      if (rawKey is String && rawKey.isNotEmpty) {
        keys.add(rawKey);
      }
    }
    return keys;
  }

  Future<void> dismissIssue({
    required String deviceId,
    required String issueKey,
    required String issueType,
  }) async {
    final dio = ref.read(dioProvider);
    await dio.post(
      '/events/dismissals',
      data: {
        'device_id': deviceId,
        'issue_key': issueKey,
        'issue_type': issueType,
      },
    );

    final current = state.valueOrNull ?? <String>{};
    state = AsyncValue.data({...current, issueKey});
  }
}

final attentionDismissalsProvider =
    AsyncNotifierProvider<AttentionDismissalsNotifier, Set<String>>(
  AttentionDismissalsNotifier.new,
);
