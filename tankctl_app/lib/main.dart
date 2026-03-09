import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/api/api_constants.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';
import 'package:tankctl_app/features/dashboard/dashboard_screen.dart';
import 'package:tankctl_app/providers/app_settings_provider.dart';
import 'package:tankctl_app/providers/dashboard_provider.dart';
import 'package:tankctl_app/providers/device_provider.dart';
import 'package:tankctl_app/providers/light_provider.dart';
import 'package:tankctl_app/providers/live_updates_provider.dart';
import 'package:tankctl_app/providers/telemetry_provider.dart';

void main() {
  runApp(
    const ProviderScope(
      child: TankCtlApp(),
    ),
  );
}

class TankCtlApp extends StatelessWidget {
  const TankCtlApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const _LiveUpdatesBootstrap(
      child: _TankCtlMaterialApp(),
    );
  }
}

class _LiveUpdatesBootstrap extends ConsumerStatefulWidget {
  const _LiveUpdatesBootstrap({required this.child});

  final Widget child;

  @override
  ConsumerState<_LiveUpdatesBootstrap> createState() =>
      _LiveUpdatesBootstrapState();
}

class _LiveUpdatesBootstrapState extends ConsumerState<_LiveUpdatesBootstrap> {
  late final ProviderSubscription<AsyncValue<Map<String, dynamic>>>
      _subscription;
  late final ProviderSubscription<AsyncValue<int>> _settingsSubscription;
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _subscription = ref.listenManual(webSocketEventsProvider, _handleLiveEvent);
    _settingsSubscription = ref.listenManual(
      liveRefreshIntervalProvider,
      _handleRefreshSetting,
      fireImmediately: true,
    );
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
    ref.invalidate(deviceProvider);
    ref.invalidate(temperatureProvider);
    ref.invalidate(temperatureHistoryProvider);
    ref.invalidate(deviceShadowProvider);
    ref.invalidate(lightStateProvider);
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

    if (eventName == 'device_registered' ||
        eventName == 'device_online' ||
        eventName == 'device_offline') {
      _syncLiveState();
      return;
    }

    if (eventName == 'telemetry_received') {
      ref.invalidate(dashboardOverviewProvider);
      if (deviceId != null) {
        ref.invalidate(temperatureHistoryProvider(deviceId));
        if (deviceId == ApiConstants.defaultDeviceId) {
          ref.invalidate(temperatureProvider);
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
        if (deviceId == ApiConstants.defaultDeviceId) {
          ref.invalidate(lightStateProvider);
        }
      }
    }
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    _settingsSubscription.close();
    _subscription.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    ref.watch(webSocketEventsProvider);
    ref.watch(liveRefreshIntervalProvider);
    return widget.child;
  }
}

class _TankCtlMaterialApp extends StatelessWidget {
  const _TankCtlMaterialApp();

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TankCtl',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.system,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      home: const DashboardScreen(),
    );
  }
}
