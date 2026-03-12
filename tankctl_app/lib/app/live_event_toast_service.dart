import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:tankctl_app/app/live_event_labels.dart';

class LiveEventToastService {
  final Map<String, DateTime> _lastToastAtByEvent = {};

  Future<void> showDeviceStatusToast(String deviceId, bool isOnline) async {
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

    final label = formatDeviceLabel(deviceId);
    final message = isOnline ? '● $label is online' : '○ $label went offline';
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

  Future<void> showLightToast(String deviceId, bool lightOn) async {
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

    final label = formatDeviceLabel(deviceId);
    final message = lightOn ? '💡 $label light on' : '🔅 $label light off';
    const bgColor = Color(0xFF2A1F00);
    const textColor = Color(0xFFFFD060);

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
}
