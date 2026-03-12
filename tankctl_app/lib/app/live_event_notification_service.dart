import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:tankctl_app/app/live_event_labels.dart';
import 'package:tankctl_app/app/navigation.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';
import 'package:tankctl_app/features/tank_detail/tank_detail_screen.dart';

class LiveEventNotificationService {
  final FlutterLocalNotificationsPlugin _notificationsPlugin =
      FlutterLocalNotificationsPlugin();
  bool _notificationsReady = false;

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

  static const AndroidNotificationChannel _sensorWarningChannel =
      AndroidNotificationChannel(
        'sensor_warning_channel',
        'Sensor Warnings',
        description: 'Alerts when a device sensor may be disconnected',
        importance: Importance.high,
      );

  Future<void> initialize() async {
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
    await androidImpl?.createNotificationChannel(_sensorWarningChannel);
    await androidImpl?.requestNotificationsPermission();
    _notificationsReady = true;

    final launchDetails =
        await _notificationsPlugin.getNotificationAppLaunchDetails();
    if (launchDetails != null &&
        launchDetails.didNotificationLaunchApp &&
        launchDetails.notificationResponse?.payload != null) {
      _navigateToDevice(launchDetails.notificationResponse!.payload!);
    }
  }

  Future<void> showDeviceStatusNotification(
    String deviceId,
    bool isOnline,
  ) async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) {
      return;
    }
    if (!_notificationsReady) {
      return;
    }

    final label = formatDeviceLabel(deviceId);
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

  Future<void> showLightNotification(String deviceId, bool lightOn) async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) {
      return;
    }
    if (!_notificationsReady) {
      return;
    }

    final label = formatDeviceLabel(deviceId);
    final title = lightOn ? 'Light Turned On' : 'Light Turned Off';
    final body = lightOn ? '$label light is now on' : '$label light is now off';

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

  Future<void> showSensorWarningNotification(String deviceId) async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) {
      return;
    }
    if (!_notificationsReady) {
      return;
    }

    final label = formatDeviceLabel(deviceId);
    const title = 'No Temp Sensor';
    final body = '$label: Temperature sensor may not be connected';

    final androidDetails = AndroidNotificationDetails(
      _sensorWarningChannel.id,
      _sensorWarningChannel.name,
      channelDescription: _sensorWarningChannel.description,
      importance: Importance.high,
      priority: Priority.high,
      category: AndroidNotificationCategory.status,
      color: const Color(0xFFFFA726),
      ticker: 'TankCtl sensor warning',
    );

    await _notificationsPlugin.show(
      ('${deviceId}_sensor').hashCode & 0x7fffffff,
      title,
      body,
      NotificationDetails(android: androidDetails),
      payload: deviceId,
    );
  }

  Future<void> showSensorRecoveredNotification(String deviceId) async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) {
      return;
    }
    if (!_notificationsReady) {
      return;
    }

    final label = formatDeviceLabel(deviceId);
    const title = 'Temp Sensor Online';
    final body = '$label: Temperature sensor is back online';

    final androidDetails = AndroidNotificationDetails(
      _sensorWarningChannel.id,
      _sensorWarningChannel.name,
      channelDescription: _sensorWarningChannel.description,
      importance: Importance.defaultImportance,
      priority: Priority.defaultPriority,
      category: AndroidNotificationCategory.status,
      color: const Color(0xFF5BBFA0),
      ticker: 'TankCtl sensor recovered',
    );

    await _notificationsPlugin.show(
      ('${deviceId}_sensor_recovered').hashCode & 0x7fffffff,
      title,
      body,
      NotificationDetails(android: androidDetails),
      payload: deviceId,
    );
  }

  void _onNotificationTapped(NotificationResponse response) {
    final deviceId = response.payload;
    if (deviceId == null || deviceId.isEmpty) {
      return;
    }
    _navigateToDevice(deviceId);
  }

  void _navigateToDevice(String deviceId) {
    navigatorKey.currentState?.push(
      MaterialPageRoute<void>(
        builder: (_) => TankDetailScreen(deviceId: deviceId),
      ),
    );
  }
}
