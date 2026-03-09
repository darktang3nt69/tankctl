import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Placeholder screen for per-device detail view.
/// Navigate here from the dashboard by tapping a TankCard.
class TankDetailScreen extends ConsumerWidget {
  const TankDetailScreen({super.key, required this.deviceId});

  final String deviceId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(
        title: Text(deviceId),
        centerTitle: false,
      ),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.water_drop_outlined, size: 64, color: Colors.white24),
            const SizedBox(height: 16),
            Text(
              deviceId,
              style: Theme.of(context)
                  .textTheme
                  .headlineSmall
                  ?.copyWith(color: Colors.white),
            ),
            const SizedBox(height: 8),
            Text(
              'Detail view — coming soon',
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: Colors.white38),
            ),
          ],
        ),
      ),
    );
  }
}
