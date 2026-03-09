import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _liveRefreshIntervalKey = 'live_refresh_interval_seconds';
const _defaultLiveRefreshIntervalSeconds = 3;

class AppSettingsNotifier extends AsyncNotifier<int> {
  @override
  Future<int> build() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(_liveRefreshIntervalKey) ??
        _defaultLiveRefreshIntervalSeconds;
  }

  Future<void> setLiveRefreshInterval(int seconds) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_liveRefreshIntervalKey, seconds);
    state = AsyncValue.data(seconds);
  }
}

final liveRefreshIntervalProvider =
    AsyncNotifierProvider<AppSettingsNotifier, int>(AppSettingsNotifier.new);