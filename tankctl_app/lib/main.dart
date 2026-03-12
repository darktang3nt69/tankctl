import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/app/live_updates_bootstrap.dart';
import 'package:tankctl_app/app/tankctl_material_app.dart';

void main() {
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
