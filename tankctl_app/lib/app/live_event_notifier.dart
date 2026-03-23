import 'package:tankctl_app/app/live_event_toast_service.dart';

class LiveEventNotifier {
  final LiveEventToastService _toastService = LiveEventToastService();

  Future<void> showDeviceStatusToast(String deviceId, bool isOnline) async {
    await _toastService.showDeviceStatusToast(deviceId, isOnline);
  }

  Future<void> showLightToast(String deviceId, bool lightOn) async {
    await _toastService.showLightToast(deviceId, lightOn);
  }
}
