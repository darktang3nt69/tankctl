import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/app/live_event_notifier.dart';
import 'package:tankctl_app/providers/app_settings_provider.dart';
import 'package:tankctl_app/providers/app_update_provider.dart';
import 'package:tankctl_app/providers/dashboard_provider.dart';
import 'package:tankctl_app/providers/device_provider.dart';
import 'package:tankctl_app/providers/light_provider.dart';
import 'package:tankctl_app/providers/live_updates_provider.dart';
import 'package:tankctl_app/providers/telemetry_provider.dart';
import 'package:tankctl_app/services/telemetry_service.dart'
    show normalizeTemperatureReading;

class LiveUpdatesBootstrap extends ConsumerStatefulWidget {
  const LiveUpdatesBootstrap({super.key, required this.child});

  final Widget child;

  @override
  ConsumerState<LiveUpdatesBootstrap> createState() =>
      _LiveUpdatesBootstrapState();
}

class _LiveUpdatesBootstrapState extends ConsumerState<LiveUpdatesBootstrap>
    with WidgetsBindingObserver {
  late final ProviderSubscription<AsyncValue<Map<String, dynamic>>>
      _subscription;
  late final ProviderSubscription<AsyncValue<int>> _settingsSubscription;
  Timer? _refreshTimer;
  final Map<String, bool> _sensorUnavailableActiveByDevice = {};
  final LiveEventNotifier _notifier = LiveEventNotifier();
  bool _isInForeground = true;
  DateTime? _lastUpdateCheck;

  static const _updateCheckThreshold = Duration(hours: 12);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _subscription = ref.listenManual(webSocketEventsProvider, _handleLiveEvent);
    _settingsSubscription = ref.listenManual(
      liveRefreshIntervalProvider,
      _handleRefreshSetting,
      fireImmediately: true,
    );
    unawaited(_notifier.initialize());
    unawaited(_triggerUpdateCheck());
  }

  void _handleRefreshSetting(AsyncValue<int>? previous, AsyncValue<int> next) {
    final seconds = next.valueOrNull;
    if (seconds == null) {
      return;
    }

    _refreshTimer?.cancel();
    _refreshTimer = Timer.periodic(
      Duration(seconds: seconds),
      (_) => _syncLiveState(),
    );
  }

  void _syncLiveState() {
    ref.invalidate(devicesListProvider);
    ref.invalidate(dashboardOverviewProvider);
    ref.invalidate(singleDeviceProvider);
    ref.invalidate(temperatureHistoryProvider);
    ref.invalidate(deviceShadowProvider);
  }

  void _handleLiveEvent(
    AsyncValue<Map<String, dynamic>>? previous,
    AsyncValue<Map<String, dynamic>> next,
  ) {
    final event = next.valueOrNull;
    if (event == null) {
      return;
    }

    final eventName = event['event'] as String?;
    final deviceId = event['device_id'] as String?;

    if (eventName == 'device_registered') {
      _syncLiveState();
      return;
    }

    if (eventName == 'device_online' || eventName == 'device_offline') {
      if (deviceId != null) {
        unawaited(
          _notifier.showDeviceStatus(
            deviceId,
            eventName == 'device_online',
            isInForeground: _isInForeground,
          ),
        );
      }
      _syncLiveState();
      return;
    }

    if (eventName == 'telemetry_received') {
      ref.invalidate(dashboardOverviewProvider);
      if (deviceId != null) {
        ref.read(lastTelemetryTimeProvider(deviceId).notifier).state =
            DateTime.now();
        ref.invalidate(temperatureHistoryProvider(deviceId));
        final metrics = event['metadata'] as Map<String, dynamic>?;
        if (normalizeTemperatureReading(metrics?['temperature']) != null) {
          ref.read(deviceWarningProvider(deviceId).notifier).state = null;
          final hadSensorOutage =
              _sensorUnavailableActiveByDevice[deviceId] ?? false;
          if (hadSensorOutage) {
            _sensorUnavailableActiveByDevice[deviceId] = false;
            final sensorWarningsEnabled = ref
                    .read(sensorWarningNotificationsEnabledProvider)
                    .valueOrNull ??
                true;
            if (sensorWarningsEnabled) {
              unawaited(_notifier.showSensorRecovered(deviceId));
            }
          }
        }
      }
      return;
    }

    if (eventName == 'device_warning') {
      if (deviceId != null) {
        final metadata = event['metadata'] as Map<String, dynamic>?;
        final code = metadata?['code'] as String? ?? 'unknown';
        ref.read(deviceWarningProvider(deviceId).notifier).state = code;
        if (code == 'sensor_unavailable') {
          final alreadyActive =
              _sensorUnavailableActiveByDevice[deviceId] ?? false;
          _sensorUnavailableActiveByDevice[deviceId] = true;

          if (!alreadyActive) {
            final sensorWarningsEnabled = ref
                    .read(sensorWarningNotificationsEnabledProvider)
                    .valueOrNull ??
                true;
            if (sensorWarningsEnabled) {
              unawaited(_notifier.showSensorWarning(deviceId));
            }
          }
        }
      }
      return;
    }

    if (eventName == 'light_state_changed' ||
        eventName == 'shadow_synchronized' ||
        eventName == 'shadow_drifted' ||
        eventName == 'command_sent' ||
        eventName == 'command_executed' ||
        eventName == 'command_failed') {
      ref.invalidate(dashboardOverviewProvider);
      if (deviceId != null) {
        ref.invalidate(deviceShadowProvider(deviceId));
        ref.invalidate(lightStateFamilyProvider(deviceId));

        if (eventName == 'light_state_changed') {
          final metadata = event['metadata'] as Map<String, dynamic>?;
          final lightState = metadata?['light'] as String?;
          if (lightState != null) {
            final lightOn = lightState == 'on';
            unawaited(
              _notifier.showLightState(
                deviceId,
                lightOn,
                isInForeground: _isInForeground,
              ),
            );
          }
        }
      }
    }
  }

  Future<void> _triggerUpdateCheck() async {
    _lastUpdateCheck = DateTime.now();
    await ref.read(appUpdateProvider.notifier).checkForUpdate();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _refreshTimer?.cancel();
    _settingsSubscription.close();
    _subscription.close();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    _isInForeground = state == AppLifecycleState.resumed;
    if (state == AppLifecycleState.resumed) {
      final last = _lastUpdateCheck;
      if (last == null ||
          DateTime.now().difference(last) > _updateCheckThreshold) {
        unawaited(_triggerUpdateCheck());
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    ref.watch(webSocketEventsProvider);
    ref.watch(liveRefreshIntervalProvider);
    return widget.child;
  }
}
