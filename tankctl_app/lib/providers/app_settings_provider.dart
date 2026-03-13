
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tankctl_app/core/api/api_constants.dart';

const _updateCheckFrequencyKey = 'update_check_frequency_hours';
const _defaultUpdateCheckFrequencyHours = 24;

class UpdateCheckFrequencyNotifier extends AsyncNotifier<int> {
  @override
  Future<int> build() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(_updateCheckFrequencyKey) ?? _defaultUpdateCheckFrequencyHours;
  }

  Future<void> setFrequency(int hours) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_updateCheckFrequencyKey, hours);
    state = AsyncValue.data(hours);
  }
}

final updateCheckFrequencyProvider =
    AsyncNotifierProvider<UpdateCheckFrequencyNotifier, int>(UpdateCheckFrequencyNotifier.new);

const _liveRefreshIntervalKey = 'live_refresh_interval_seconds';
const _defaultLiveRefreshIntervalSeconds = 3;
const _serverBaseUrlKey = 'server_base_url';
const _sensorWarningsEnabledKey = 'sensor_warning_notifications_enabled';

String _normalizeServerUrl(String raw) {
  final trimmed = raw.trim();
  if (trimmed.isEmpty) {
    throw const FormatException('Server URL cannot be empty');
  }

  final withScheme = trimmed.contains('://') ? trimmed : 'http://$trimmed';
  final uri = Uri.tryParse(withScheme);
  if (uri == null || uri.host.isEmpty) {
    throw const FormatException('Enter a valid server URL');
  }

  final normalized = uri
      .replace(path: '', query: null, fragment: null)
      .toString();
  return normalized.endsWith('/')
      ? normalized.substring(0, normalized.length - 1)
      : normalized;
}

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

class ServerBaseUrlNotifier extends AsyncNotifier<String> {
  @override
  Future<String> build() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_serverBaseUrlKey) ?? ApiConstants.baseUrl;
  }

  Future<void> setServerBaseUrl(String rawUrl) async {
    final normalized = _normalizeServerUrl(rawUrl);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_serverBaseUrlKey, normalized);
    state = AsyncValue.data(normalized);
  }
}

final serverBaseUrlProvider =
    AsyncNotifierProvider<ServerBaseUrlNotifier, String>(
      ServerBaseUrlNotifier.new,
    );

class SensorWarningNotificationsNotifier extends AsyncNotifier<bool> {
  @override
  Future<bool> build() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_sensorWarningsEnabledKey) ?? true;
  }

  Future<void> setEnabled(bool enabled) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_sensorWarningsEnabledKey, enabled);
    state = AsyncValue.data(enabled);
  }
}

final sensorWarningNotificationsEnabledProvider =
    AsyncNotifierProvider<SensorWarningNotificationsNotifier, bool>(
      SensorWarningNotificationsNotifier.new,
    );