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

Future<void> _initializeFirebaseSafely() async {
  try {
    // On Android/iOS with native firebase config files, the default app may
    // already exist. Calling initializeApp() without options reuses it.
    if (Platform.isAndroid || Platform.isIOS || Platform.isMacOS) {
      await Firebase.initializeApp();
    } else {
      await Firebase.initializeApp(
        options: DefaultFirebaseOptions.currentPlatform,
      );
    }
  } on FirebaseException catch (e) {
    if (e.code != 'duplicate-app') {
      rethrow;
    }
  }
}

/// Top-level background message handler for FCM
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await _initializeFirebaseSafely();
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
  await _initializeFirebaseSafely();

  // Must be registered before the isolate starts (background handler requirement).
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

  // Render the app immediately — no black screen.
  runApp(const ProviderScope(child: TankCtlApp()));

  // All non-critical startup work happens after the first frame is on screen.
  _postRunAppInit();
}

/// Everything that should NOT block the first frame goes here.
Future<void> _postRunAppInit() async {
  // Notification permission (Android 13+) — can happen after first frame.
  if (Platform.isAndroid) {
    await FirebaseMessaging.instance.requestPermission();
  }

  // Local notification service initialisation.
  final notificationService = LiveEventNotificationService();
  await notificationService.initialize();

  // Wire up foreground FCM message display.
  FirebaseMessaging.onMessage.listen((RemoteMessage message) async {
    final data = message.data;
    final deviceId = data['device_id'] ?? ApiConstants.defaultDeviceId;
    if (message.notification != null) {
      await notificationService.showSimpleNotification(
        message.notification!.title,
        message.notification!.body,
        payload: deviceId,
        data: data,
      );
    }
  });

  // Notification tap while app is in background/terminated.
  FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
    final deviceId = message.data['device_id'] ?? ApiConstants.defaultDeviceId;
    navigatorKey.currentState?.pushNamed('/device/$deviceId');
  });

  // FCM token registration — network call, must not block startup.
  final deviceIdForFcm = await _getDeviceIdForFcm();

  Future<void> registerFcmToken(String? token) async {
    if (token == null) return;
    try {
      await Dio().post(
        '${ApiConstants.baseUrl}/mobile/push-token',
        data: {
          'device_id': deviceIdForFcm,
          'token': token,
          'platform': 'android',
        },
        options: Options(headers: {'Content-Type': 'application/json'}),
      );
    } catch (_) {
      // Non-critical — token will be re-registered on next launch / refresh.
    }
  }

  final token = await FirebaseMessaging.instance.getToken();
  await registerFcmToken(token);

  FirebaseMessaging.instance.onTokenRefresh.listen(registerFcmToken);
}

class TankCtlApp extends StatelessWidget {
  const TankCtlApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const LiveUpdatesBootstrap(child: TankCtlMaterialApp());
  }
}
