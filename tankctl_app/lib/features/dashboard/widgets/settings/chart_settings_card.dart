import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/features/dashboard/widgets/settings/settings_card_shell.dart';
import 'package:tankctl_app/providers/app_settings_provider.dart';

class ChartSettingsCard extends ConsumerWidget {
  const ChartSettingsCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final textTheme = Theme.of(context).textTheme;
    final deselectSecondsAsync = ref.watch(chartPointDeselectSecondsProvider);

    return SettingsCardShell(
      child: deselectSecondsAsync.when(
        data: (seconds) => Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.show_chart_rounded),
                const SizedBox(width: 10),
                Text(
                  'Chart Point Display',
                  style: textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                const Icon(Icons.timer_rounded),
                const SizedBox(width: 10),
                Text(
                  'Auto-deselect timer',
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
                    .read(chartPointDeselectSecondsProvider.notifier)
                    .setDeselectSeconds(value.round());
              },
            ),
            const SizedBox(height: 8),
            Text(
              'Time before tapped point fades away when viewing temperature charts.',
              style: textTheme.bodySmall?.copyWith(color: Colors.white54),
            ),
          ],
        ),
        loading: () => const SizedBox(
          height: 80,
          child: Center(child: CircularProgressIndicator()),
        ),
        error: (error, _) => Text(
          'Could not load chart settings: $error',
          style: textTheme.bodyMedium?.copyWith(color: Colors.redAccent),
        ),
      ),
    );
  }
}
