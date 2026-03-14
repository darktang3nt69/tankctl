import 'package:flutter/material.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';
import 'package:tankctl_app/utils/app_icons.dart';

/// Small status indicator with icon/label showing device online/offline state.
class StatusIndicator extends StatelessWidget {
  const StatusIndicator({super.key, required this.isOnline});

  final bool isOnline;

  @override
  Widget build(BuildContext context) {
    final color = isOnline ? TankCtlColors.success : TankCtlColors.temperature;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          isOnline ? AppIcons.wifiStrong : AppIcons.wifiOff,
          size: 16,
          color: color,
        ),
        const SizedBox(width: 6),
        Text(
          isOnline ? 'Online' : 'Offline',
          style: TextStyle(
            color: color,
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}
