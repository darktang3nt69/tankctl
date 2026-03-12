import 'package:tankctl_app/app/live_event_notification_service.dart';
import 'package:tankctl_app/app/live_event_toast_service.dart';

class LiveEventNotifier {
  final LiveEventToastService _toastService = LiveEventToastService();
  final LiveEventNotificationService _notificationService =
      LiveEventNotificationService();

  Future<void> initialize() async {
    await _notificationService.initialize();
  }

  Future<void> showDeviceStatus(
    String deviceId,
    bool isOnline, {
    required bool isInForeground,
  }) async {
    if (isInForeground) {
      await _toastService.showDeviceStatusToast(deviceId, isOnline);
      return;
    }
    await _notificationService.showDeviceStatusNotification(deviceId, isOnline);
  }

  Future<void> showLightState(
    String deviceId,
    bool lightOn, {
    required bool isInForeground,
  }) async {
    if (isInForeground) {
      await _toastService.showLightToast(deviceId, lightOn);
      return;
    }
    await _notificationService.showLightNotification(deviceId, lightOn);
  }

  Future<void> showSensorWarning(String deviceId) async {
    await _notificationService.showSensorWarningNotification(deviceId);
  }

  Future<void> showSensorRecovered(String deviceId) async {
    await _notificationService.showSensorRecoveredNotification(deviceId);
  }
}
