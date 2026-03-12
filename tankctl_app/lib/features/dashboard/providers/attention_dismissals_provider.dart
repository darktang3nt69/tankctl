import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/services/device_service.dart';

class AttentionDismissalsNotifier extends AsyncNotifier<Set<String>> {
  @override
  Future<Set<String>> build() async {
    return _fetchDismissedIssueKeys();
  }

  Future<Set<String>> _fetchDismissedIssueKeys() async {
    return ref.read(deviceServiceProvider).getAcknowledgedIssueKeys();
  }

  Future<void> dismissIssue({
    required String deviceId,
    required String warningCode,
  }) async {
    // Backend remains the source of truth; no local optimistic merge.
    await ref.read(deviceServiceProvider).acknowledgeWarning(deviceId, warningCode);
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetchDismissedIssueKeys);
  }
}

final attentionDismissalsProvider =
    AsyncNotifierProvider<AttentionDismissalsNotifier, Set<String>>(
  AttentionDismissalsNotifier.new,
);
