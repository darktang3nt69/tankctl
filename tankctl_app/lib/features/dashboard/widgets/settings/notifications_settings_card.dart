import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/features/dashboard/widgets/settings/settings_card_shell.dart';
import 'package:tankctl_app/providers/app_settings_provider.dart';

class NotificationsSettingsCard extends ConsumerWidget {
  const NotificationsSettingsCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final textTheme = Theme.of(context).textTheme;
    final sensorWarningsEnabledAsync = ref.watch(
      sensorWarningNotificationsEnabledProvider,
    );

    return SettingsCardShell(
      child: sensorWarningsEnabledAsync.when(
        data: (enabled) => SwitchListTile.adaptive(
          contentPadding: EdgeInsets.zero,
          title: const Text('Sensor warning notifications'),
          subtitle: Text(
            enabled ? 'Enabled' : 'Muted',
            style: textTheme.bodySmall?.copyWith(color: Colors.white60),
          ),
          value: enabled,
          onChanged: (value) => ref
              .read(sensorWarningNotificationsEnabledProvider.notifier)
              .setEnabled(value),
        ),
        loading: () => const SizedBox(
          height: 56,
          child: Center(child: CircularProgressIndicator()),
        ),
        error: (error, _) => Text(
          'Could not load notification settings: $error',
          style: textTheme.bodyMedium?.copyWith(color: Colors.redAccent),
        ),
      ),
    );
  }
}
