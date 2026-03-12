import 'package:flutter_local_notifications/flutter_local_notifications.dart';

const deviceStatusChannel = AndroidNotificationChannel(
  'device_status_channel',
  'Device Status',
  description: 'Online/offline status updates for tank devices',
  importance: Importance.high,
);

const lightStateChannel = AndroidNotificationChannel(
  'light_state_channel',
  'Light State',
  description: 'Light on/off changes for tank devices',
  importance: Importance.defaultImportance,
);

const sensorWarningChannel = AndroidNotificationChannel(
  'sensor_warning_channel',
  'Sensor Warnings',
  description: 'Alerts when a device sensor may be disconnected',
  importance: Importance.high,
);
