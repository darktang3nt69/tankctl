import 'package:flutter/material.dart';
import 'package:fluentui_system_icons/fluentui_system_icons.dart';

/// Central icon mapping: Fluent UI System Icons
/// Maps semantic icon names to Fluent UI icon resources
class AppIcons {
  // Status & general
  static const IconData checkCircle = FluentIcons.checkmark_24_filled;
  static const IconData check = FluentIcons.checkmark_24_regular;
  static const IconData warning = FluentIcons.warning_24_regular;
  static const IconData error = FluentIcons.error_circle_24_regular;
  static const IconData info = FluentIcons.warning_24_regular;
  static const IconData help = FluentIcons.warning_24_regular;

  // Devices & connectivity
  static const IconData cloudOff = FluentIcons.cloud_off_24_regular;
  static const IconData cloudOffOutlined = FluentIcons.cloud_off_24_regular;
  static const IconData wifiStrong = FluentIcons.wifi_4_24_regular;
  static const IconData wifiMedium = FluentIcons.wifi_2_24_regular;
  static const IconData wifiWeak = FluentIcons.wifi_1_24_regular;
  static const IconData wifiOff = FluentIcons.wifi_off_24_regular;
  static const IconData sensorsOff = FluentIcons.alert_off_24_regular;
  static const IconData reload = FluentIcons.arrow_sync_24_regular;

  // Lighting
  static const IconData lightOn = FluentIcons.lightbulb_24_filled;
  static const IconData lightOff = FluentIcons.lightbulb_24_regular;
  static const IconData nightlight = FluentIcons.lightbulb_24_regular;

  // Actions
  static const IconData reboot = FluentIcons.arrow_sync_24_regular;
  static const IconData refresh = FluentIcons.arrow_sync_24_regular;
  static const IconData edit = FluentIcons.edit_24_regular;
  static const IconData close = FluentIcons.dismiss_24_regular;
  static const IconData moreHoriz = FluentIcons.more_horizontal_24_regular;

  // Sensor / Temperature
  static const IconData thermostat = FluentIcons.shield_24_regular;
  static const IconData acUnit = FluentIcons.record_24_regular;
  static const IconData verified = FluentIcons.checkmark_24_filled;

  // Settings & UI
  static const IconData dns = FluentIcons.server_24_regular;
  static const IconData systemUpdate = FluentIcons.arrow_sync_24_regular;
  static const IconData time = FluentIcons.clock_24_regular;
  static const IconData flash = FluentIcons.flash_24_filled;

  // Device status indicator (FAB icon mapping)
  static IconData getStatusIcon(String status) {
    switch (status) {
      case 'offline':
        return AppIcons.cloudOff;
      case 'highTemp':
      case 'lowTemp':
      case 'unknown':
        return AppIcons.warning;
      case 'healthy':
      case 'ok':
      default:
        return AppIcons.checkCircle;
    }
  }
}
