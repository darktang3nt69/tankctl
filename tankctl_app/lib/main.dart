import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tankctl_app/app/live_updates_bootstrap.dart';
import 'package:tankctl_app/app/navigation.dart';
import 'package:tankctl_app/app/tankctl_material_app.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'dart:io';
import 'package:dio/dio.dart';
import 'firebase_options.dart';
import 'core/api/api_constants.dart';
import 'app/live_event_notification_service.dart';

const _selectedDeviceIdKey = 'selected_device_id_for_fcm';

/// Top-level background message handler for FCM
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  // You can show a local notification here if needed
}

/// Fetch the first available device from the backend API
Future<String> _getFirstDeviceId() async {
  try {
    final dio = Dio();
    final response = await dio.get(
      '${ApiConstants.baseUrl}/devices',
      options: Options(
        connectTimeout: const Duration(seconds: 5),
        receiveTimeout: const Duration(seconds: 5),
      ),
    );

    final data = response.data as Map<String, dynamic>?;
    final devices = data?['devices'] as List?;

    if (devices != null && devices.isNotEmpty) {
      final firstDevice = devices[0] as Map<String, dynamic>;
      return firstDevice['device_id'] as String? ??
          ApiConstants.defaultDeviceId;
    }
  } catch (e) {
    // Fall through to use stored or default device ID
  }
  return ApiConstants.defaultDeviceId;
}

/// Get the device ID to use for FCM registration
Future<String> _getDeviceIdForFcm() async {
  try {
    // Try to get from stored preference first
    final prefs = await SharedPreferences.getInstance();
    final stored = prefs.getString(_selectedDeviceIdKey);
    if (stored != null && stored.isNotEmpty) {
      return stored;
    }

    // Otherwise fetch the first device and cache it
    final deviceId = await _getFirstDeviceId();
    await prefs.setString(_selectedDeviceIdKey, deviceId);
    return deviceId;
  } catch (e) {
    return ApiConstants.defaultDeviceId;
  }
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);

  // Register background handler
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
  // Request notification permission (Android 13+)
  if (Platform.isAndroid) {
    final messaging = FirebaseMessaging.instance;
    await messaging.requestPermission();
  }

  // Initialize local notification service
  final notificationService = LiveEventNotificationService();
  await notificationService.initialize();

  // Get the device ID to use for this app
  final deviceIdForFcm = await _getDeviceIdForFcm();

  // Helper to register FCM token with backend
  Future<void> registerFcmToken(String? token) async {
    if (token != null) {
      try {
        final backendUrl = '${ApiConstants.baseUrl}/mobile/push-token';
        await Dio().post(
          backendUrl,
          data: {
            'device_id': deviceIdForFcm,
            'token': token,
            'platform': 'android',
          },
          options: Options(headers: {'Content-Type': 'application/json'}),
        );
        // Show a toast/snackbar for user feedback (if context available)
      } catch (e) {
        // Optionally show error feedback to user
      }
    }
  }

  // Register current token on startup
  final token = await FirebaseMessaging.instance.getToken();
  await registerFcmToken(token);

  // Listen for token refresh and auto-register
  FirebaseMessaging.instance.onTokenRefresh.listen((newToken) async {
    await registerFcmToken(newToken);
  });

  // Foreground message handler
  FirebaseMessaging.onMessage.listen((RemoteMessage message) async {
    // Show a local notification for FCM message
    final data = message.data;
    final deviceId = data['device_id'] ?? ApiConstants.defaultDeviceId;
    if (message.notification != null) {
      // Use notification title/body if present
      await notificationService.showSimpleNotification(
        message.notification!.title,
        message.notification!.body,
        payload: deviceId,
        data: data,
      );
    }
  });

  // Notification tap handler (when app is opened from notification)
  FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
    final deviceId = message.data['device_id'] ?? ApiConstants.defaultDeviceId;
    navigatorKey.currentState?.pushNamed('/device/$deviceId');
  });

  runApp(const ProviderScope(child: TankCtlApp()));
}

class TankCtlApp extends StatelessWidget {
  const TankCtlApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const LiveUpdatesBootstrap(child: TankCtlMaterialApp());
  }
}
