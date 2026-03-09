import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/api/api_constants.dart';
import 'package:tankctl_app/services/light_service.dart';

class LightNotifier extends AsyncNotifier<bool> {
  @override
  Future<bool> build() {
    return ref
        .watch(lightServiceProvider)
        .getLightState(ApiConstants.defaultDeviceId);
  }

  /// Sends the light command to the backend and optimistically updates state.
  Future<void> toggle(bool on) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      await ref
          .read(lightServiceProvider)
          .setLight(ApiConstants.defaultDeviceId, on);
      return on;
    });
  }
}

final lightStateProvider =
    AsyncNotifierProvider<LightNotifier, bool>(LightNotifier.new);

/// Per-device light notifier used by individual tank cards.
class LightFamilyNotifier extends FamilyAsyncNotifier<bool, String> {
  @override
  Future<bool> build(String deviceId) {
    return ref.watch(lightServiceProvider).getLightState(deviceId);
  }

  Future<void> toggle(bool on) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      await ref.read(lightServiceProvider).setLight(arg, on);
      return on;
    });
  }
}

final lightStateFamilyProvider = AsyncNotifierProviderFamily<
    LightFamilyNotifier, bool, String>(LightFamilyNotifier.new);
