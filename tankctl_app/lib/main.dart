import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/app/live_updates_bootstrap.dart';
import 'package:tankctl_app/app/tankctl_material_app.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'dart:io';
import 'package:dio/dio.dart';
import 'firebase_options.dart';
import 'core/api/api_constants.dart';
import 'app/live_event_notification_service.dart';

/// Top-level background message handler for FCM
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  // You can show a local notification here if needed
  print('Handling a background message: \\${message.messageId}');
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );

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

  // Helper to register FCM token with backend
  Future<void> registerFcmToken(String? token) async {
    print('FCM Token: \\${token ?? "(null)"}');
    if (token != null) {
      try {
        final backendUrl = '${ApiConstants.baseUrl}/mobile/push-token';
        await Dio().post(
          backendUrl,
          data: {
            'device_id': ApiConstants.defaultDeviceId,
            'token': token,
            'platform': 'android',
          },
          options: Options(
            headers: {'Content-Type': 'application/json'},
          ),
        );
        print('FCM token registered with backend');
        // Show a toast/snackbar for user feedback (if context available)
      } catch (e) {
        print('Failed to register FCM token: $e');
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
    print('Received FCM message in foreground: \\${message.notification?.title}');
    // Show a local notification for FCM message
    final data = message.data;
    final deviceId = data['device_id'] ?? ApiConstants.defaultDeviceId;
    if (message.notification != null) {
      // Use notification title/body if present
      await notificationService.showSimpleNotification(
        message.notification!.title,
        message.notification!.body,
        payload: deviceId,
      );
    }
  });

  // Notification tap handler (when app is opened from notification)
  FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
    print('Notification tap: \\${message.data}');
    final deviceId = message.data['device_id'] ?? ApiConstants.defaultDeviceId;
    // Example navigation: push to device detail if navigatorKey is set up
    // navigatorKey.currentState?.pushNamed('/device/$deviceId');
    // TODO: Implement navigation to device detail screen if needed
  });

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
    return const LiveUpdatesBootstrap(
      child: TankCtlMaterialApp(),
    );
  }
}
