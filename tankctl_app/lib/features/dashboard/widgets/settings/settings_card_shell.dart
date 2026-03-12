import 'package:flutter/material.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';

class SettingsCardShell extends StatelessWidget {
  const SettingsCardShell({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: TankCtlColors.card,
        borderRadius: BorderRadius.circular(16),
      ),
      child: child,
    );
  }
}
