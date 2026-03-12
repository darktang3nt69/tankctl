import 'package:flutter/material.dart';
import 'package:tankctl_app/app/navigation.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';
import 'package:tankctl_app/features/dashboard/dashboard_screen.dart';

class TankCtlMaterialApp extends StatelessWidget {
  const TankCtlMaterialApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TankCTL',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.system,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      navigatorKey: navigatorKey,
      home: const DashboardScreen(),
    );
  }
}
