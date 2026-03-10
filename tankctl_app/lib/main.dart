import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';
import 'package:tankctl_app/features/dashboard/dashboard_screen.dart';
import 'package:tankctl_app/features/tank_detail/tank_detail_screen.dart';
import 'package:tankctl_app/providers/app_settings_provider.dart';
import 'package:tankctl_app/providers/dashboard_provider.dart';
import 'package:tankctl_app/providers/device_provider.dart';
import 'package:tankctl_app/providers/light_provider.dart';
import 'package:tankctl_app/providers/live_updates_provider.dart';
import 'package:tankctl_app/providers/telemetry_provider.dart';
import 'package:tankctl_app/services/telemetry_service.dart'
    show normalizeTemperatureReading;

/// Global navigator key — allows notification tap handler to push routes
/// without a BuildContext.
final _navigatorKey = GlobalKey<NavigatorState>();

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

class _LiveUpdatesBootstrapState extends ConsumerState<_LiveUpdatesBootstrap>
    with WidgetsBindingObserver {
  late final ProviderSubscription<AsyncValue<Map<String, dynamic>>>
      _subscription;
  late final ProviderSubscription<AsyncValue<int>> _settingsSubscription;
  Timer? _refreshTimer;
  final Map<String, DateTime> _lastToastAtByEvent = {};
  final FlutterLocalNotificationsPlugin _notificationsPlugin =
      FlutterLocalNotificationsPlugin();
  bool _notificationsReady = false;
  bool _isInForeground = true;

  static const AndroidNotificationChannel _deviceStatusChannel =
      AndroidNotificationChannel(
        'device_status_channel',
        'Device Status',
        description: 'Online/offline status updates for tank devices',
        importance: Importance.high,
      );

  static const AndroidNotificationChannel _lightStateChannel =
      AndroidNotificationChannel(
        'light_state_channel',
        'Light State',
        description: 'Light on/off changes for tank devices',
        importance: Importance.defaultImportance,
      );

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
    unawaited(_initNotifications());
  }

  Future<void> _initNotifications() async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) {
      return;
    }

    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const initSettings = InitializationSettings(android: androidInit);
    await _notificationsPlugin.initialize(
      initSettings,
      onDidReceiveNotificationResponse: _onNotificationTapped,
    );

    final androidImpl = _notificationsPlugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>();
    await androidImpl?.createNotificationChannel(_deviceStatusChannel);
    await androidImpl?.createNotificationChannel(_lightStateChannel);
    await androidImpl?.requestNotificationsPermission();
    _notificationsReady = true;

    // Handle tap when app was fully terminated and launched by a notification.
    final launchDetails =
        await _notificationsPlugin.getNotificationAppLaunchDetails();
    if (launchDetails != null &&
        launchDetails.didNotificationLaunchApp &&
        launchDetails.notificationResponse?.payload != null) {
      _navigateToDevice(launchDetails.notificationResponse!.payload!);
    }
  }

  void _onNotificationTapped(NotificationResponse response) {
    final deviceId = response.payload;
    if (deviceId == null || deviceId.isEmpty) {
      return;
    }
    _navigateToDevice(deviceId);
  }

  void _navigateToDevice(String deviceId) {
    _navigatorKey.currentState?.push(
      MaterialPageRoute<void>(
        builder: (_) => TankDetailScreen(deviceId: deviceId),
      ),
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
    ref.invalidate(singleDeviceProvider);
    ref.invalidate(temperatureHistoryProvider);
    ref.invalidate(deviceShadowProvider);
  }

  Future<void> _showDeviceStatusToast(String deviceId, bool isOnline) async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) {
      return;
    }

    final eventKey = '$deviceId:${isOnline ? 'online' : 'offline'}';
    final now = DateTime.now();
    final lastShownAt = _lastToastAtByEvent[eventKey];
    if (lastShownAt != null && now.difference(lastShownAt).inSeconds < 5) {
      return;
    }
    _lastToastAtByEvent[eventKey] = now;

    final label = _formatDeviceLabel(deviceId);
    final message = isOnline ? '● $label is online' : '○ $label went offline';

    // Dark backgrounds from the app palette with high-contrast status text.
    // Avoids the washed-out look of using mid-saturation colors as backgrounds.
    final bgColor =
        isOnline ? const Color(0xFF0E2823) : const Color(0xFF2D1020);
    final textColor =
        isOnline ? const Color(0xFF5DDEB5) : const Color(0xFFFF8FAD);

    await Fluttertoast.cancel();
    await Fluttertoast.showToast(
      msg: message,
      toastLength: Toast.LENGTH_SHORT,
      gravity: ToastGravity.BOTTOM,
      backgroundColor: bgColor,
      textColor: textColor,
      fontSize: 14,
    );
  }

  Future<void> _showDeviceStatusNotification(
    String deviceId,
    bool isOnline,
  ) async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) {
      return;
    }
    if (!_notificationsReady) {
      return;
    }

    final label = _formatDeviceLabel(deviceId);
    final title = isOnline ? 'Device Online' : 'Device Offline';
    final body = isOnline ? '$label is online' : '$label went offline';

    final androidDetails = AndroidNotificationDetails(
      _deviceStatusChannel.id,
      _deviceStatusChannel.name,
      channelDescription: _deviceStatusChannel.description,
      importance: Importance.high,
      priority: Priority.high,
      category: AndroidNotificationCategory.status,
      color: isOnline ? TankCtlColors.success : TankCtlColors.temperature,
      ticker: 'TankCtl device status',
    );

    await _notificationsPlugin.show(
      deviceId.hashCode & 0x7fffffff,
      title,
      body,
      NotificationDetails(android: androidDetails),
      payload: deviceId,
    );
  }

  Future<void> _showLightToast(String deviceId, bool lightOn) async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) {
      return;
    }

    final eventKey = '$deviceId:light:${lightOn ? 'on' : 'off'}';
    final now = DateTime.now();
    final lastShownAt = _lastToastAtByEvent[eventKey];
    if (lastShownAt != null && now.difference(lastShownAt).inSeconds < 5) {
      return;
    }
    _lastToastAtByEvent[eventKey] = now;

    final label = _formatDeviceLabel(deviceId);
    final message = lightOn ? '💡 $label light on' : '🔅 $label light off';
    final bgColor = const Color(0xFF2A1F00);
    final textColor = const Color(0xFFFFD060);

    await Fluttertoast.cancel();
    await Fluttertoast.showToast(
      msg: message,
      toastLength: Toast.LENGTH_SHORT,
      gravity: ToastGravity.BOTTOM,
      backgroundColor: bgColor,
      textColor: textColor,
      fontSize: 14,
    );
  }

  Future<void> _showLightNotification(String deviceId, bool lightOn) async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) {
      return;
    }
    if (!_notificationsReady) {
      return;
    }

    final label = _formatDeviceLabel(deviceId);
    final title = lightOn ? 'Light Turned On' : 'Light Turned Off';
    final body  = lightOn ? '$label light is now on' : '$label light is now off';

    final androidDetails = AndroidNotificationDetails(
      _lightStateChannel.id,
      _lightStateChannel.name,
      channelDescription: _lightStateChannel.description,
      importance: Importance.defaultImportance,
      priority: Priority.defaultPriority,
      category: AndroidNotificationCategory.status,
      color: lightOn ? const Color(0xFFFFD060) : TankCtlColors.primary,
      ticker: 'TankCtl light state',
    );

    await _notificationsPlugin.show(
      ('${deviceId}_light').hashCode & 0x7fffffff,
      title,
      body,
      NotificationDetails(android: androidDetails),
      payload: deviceId,
    );
  }

  String _formatDeviceLabel(String deviceId) {
    final normalized = deviceId.replaceAll(RegExp(r'[_-]+'), ' ').trim();
    if (normalized.isEmpty) {
      return deviceId;
    }

    return normalized
        .split(RegExp(r'\s+'))
        .map((word) {
          if (word.isEmpty) {
            return word;
          }
          final lower = word.toLowerCase();
          return '${lower[0].toUpperCase()}${lower.substring(1)}';
        })
        .join(' ');
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
        if (_isInForeground) {
          unawaited(
            _showDeviceStatusToast(deviceId, eventName == 'device_online'),
          );
        } else {
          unawaited(
            _showDeviceStatusNotification(
              deviceId,
              eventName == 'device_online',
            ),
          );
        }
      }
      _syncLiveState();
      return;
    }

    if (eventName == 'telemetry_received') {
      ref.invalidate(dashboardOverviewProvider);
      if (deviceId != null) {
        // Stamp the last-seen time so TankCard can show "Xs ago"
        ref.read(lastTelemetryTimeProvider(deviceId).notifier).state =
            DateTime.now();
        ref.invalidate(temperatureHistoryProvider(deviceId));
        // Clear any sensor warning once a valid temperature arrives.
        final metrics = event['metadata'] as Map<String, dynamic>?;
        if (normalizeTemperatureReading(metrics?['temperature']) != null) {
          ref.read(deviceWarningProvider(deviceId).notifier).state = null;
        }
      }
      return;
    }

    if (eventName == 'device_warning') {
      if (deviceId != null) {
        final metadata = event['metadata'] as Map<String, dynamic>?;
        final code = metadata?['code'] as String? ?? 'unknown';
        ref.read(deviceWarningProvider(deviceId).notifier).state = code;
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
            if (_isInForeground) {
              unawaited(_showLightToast(deviceId, lightOn));
            } else {
              unawaited(_showLightNotification(deviceId, lightOn));
            }
          }
        }
      }
    }
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
      navigatorKey: _navigatorKey,
      home: const DashboardScreen(),
    );
  }
}
