import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/features/dashboard/widgets/settings/settings_card_shell.dart';
import 'package:tankctl_app/providers/app_settings_provider.dart';

class LiveUpdatesSettingsCard extends ConsumerWidget {
  const LiveUpdatesSettingsCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final textTheme = Theme.of(context).textTheme;
    final refreshIntervalAsync = ref.watch(liveRefreshIntervalProvider);

    return SettingsCardShell(
      child: refreshIntervalAsync.when(
        data: (seconds) => Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.bolt_rounded),
                const SizedBox(width: 10),
                Text(
                  'Live refresh interval',
                  style: textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const Spacer(),
                Text(
                  '$seconds s',
                  style: textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Slider(
              value: seconds.toDouble(),
              min: 1,
              max: 10,
              divisions: 9,
              label: '$seconds s',
              onChanged: (value) {
                ref
                    .read(liveRefreshIntervalProvider.notifier)
                    .setLiveRefreshInterval(value.round());
              },
            ),
            const SizedBox(height: 8),
            Text(
              'Recommended: 3-5 seconds. Lower values feel more instant but send more HTTP refresh traffic.',
              style: textTheme.bodySmall?.copyWith(color: Colors.white54),
            ),
          ],
        ),
        loading: () => const SizedBox(
          height: 80,
          child: Center(child: CircularProgressIndicator()),
        ),
        error: (error, _) => Text(
          'Could not load settings: $error',
          style: textTheme.bodyMedium?.copyWith(color: Colors.redAccent),
        ),
      ),
    );
  }
}
