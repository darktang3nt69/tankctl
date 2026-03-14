import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class LiveEventNotificationService {
  final FlutterLocalNotificationsPlugin _notificationsPlugin = FlutterLocalNotificationsPlugin();
  bool _notificationsReady = false;

  /// Improve notification title based on type
  static String _formatTitle(String type, String? originalTitle) {
    if (originalTitle != null && originalTitle.isNotEmpty) {
      return originalTitle;
    }
    switch (type) {
      case 'light_on':
        return '💡 Light ON';
      case 'light_off':
        return '🌙 Light OFF';
      case 'device_online':
        return '✅ Device Online';
      case 'device_offline':
        return '🚨 Device Offline';
      case 'temperature_high':
        return '🔥 Temperature Alert';
      case 'temperature_low':
        return '❄️ Temperature Alert';
      case 'warning':
        return '⚠️ Warning';
      default:
        return originalTitle ?? 'TankCtl';
    }
  }

  Future<void> showSimpleNotification(String? title, String? body, {String? payload, Map<String, dynamic>? data}) async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) {
      return;
    }
    if (!_notificationsReady) {
      return;
    }

    // Extract notification type from data payload
    final notificationType = data?['notification_type'] as String? ?? 'info';
    final formattedTitle = _formatTitle(notificationType, title);

    // Build big text style for longer messages
    final androidStyle = BigTextStyleInformation(
      body ?? '',
      contentTitle: formattedTitle,
      summaryText: 'TankCtl Alert',
      htmlFormatContent: false,
      htmlFormatTitle: false,
    );

    final androidDetails = AndroidNotificationDetails(
      'tankctl_notifications', // Channel ID
      'TankCtl Notifications', // Channel name
      channelDescription: 'Notifications for device alerts and status updates',
      importance: Importance.high,
      priority: Priority.high,
      enableVibration: true,
      playSound: true,
      sound: RawResourceAndroidNotificationSound('notification'),
      styleInformation: androidStyle,
      // Use emoji/unicode for visual distinction
      shortcutId: notificationType,
    );

    final notificationDetails = NotificationDetails(android: androidDetails);

    await _notificationsPlugin.show(
      DateTime.now().millisecondsSinceEpoch ~/ 1000,
      formattedTitle,
      body,
      notificationDetails,
      payload: payload,
    );
  }

  Future<void> initialize() async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) {
      return;
    }
    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const initSettings = InitializationSettings(android: androidInit);
    await _notificationsPlugin.initialize(
      initSettings,
    );
    _notificationsReady = true;
  }
}