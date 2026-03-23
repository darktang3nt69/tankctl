import 'package:flutter/material.dart';
import 'package:tankctl_app/utils/app_icons.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/api/api_constants.dart';
import 'package:tankctl_app/features/dashboard/widgets/settings/settings_card_shell.dart';
import 'package:tankctl_app/providers/app_settings_provider.dart';
import 'package:tankctl_app/providers/dashboard_provider.dart';
import 'package:tankctl_app/providers/device_provider.dart';
import 'package:tankctl_app/providers/telemetry_provider.dart';

class BackendSettingsCard extends ConsumerWidget {
  const BackendSettingsCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final textTheme = Theme.of(context).textTheme;
    final serverUrlAsync = ref.watch(serverBaseUrlProvider);

    return SettingsCardShell(
      child: serverUrlAsync.when(
        data: (serverUrl) => Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(AppIcons.dns),
                const SizedBox(width: 10),
                Text(
                  'Server URL',
                  style: textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            SelectableText(
              serverUrl,
              style: textTheme.bodyMedium?.copyWith(color: Colors.white70),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                FilledButton.icon(
                  onPressed: () => _changeUrl(context, ref, serverUrl),
                  icon: const Icon(AppIcons.edit),
                  label: const Text('Change URL'),
                ),
                const SizedBox(width: 10),
                OutlinedButton(
                  onPressed: () => _resetToDefault(context, ref),
                  child: const Text('Use Default'),
                ),
              ],
            ),
          ],
        ),
        loading: () => const SizedBox(
          height: 80,
          child: Center(child: CircularProgressIndicator()),
        ),
        error: (error, _) => Text(
          'Could not load server URL: $error',
          style: textTheme.bodyMedium?.copyWith(color: Colors.redAccent),
        ),
      ),
    );
  }

  Future<void> _changeUrl(
    BuildContext context,
    WidgetRef ref,
    String serverUrl,
  ) async {
    final controller = TextEditingController(text: serverUrl);
    final submitted = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Backend Server URL'),
        content: TextField(
          controller: controller,
          keyboardType: TextInputType.url,
          decoration: const InputDecoration(
            hintText: 'http://192.168.1.100:8000',
          ),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(controller.text),
            child: const Text('Save'),
          ),
        ],
      ),
    );
    controller.dispose();

    if (submitted == null) {
      return;
    }

    try {
      await ref.read(serverBaseUrlProvider.notifier).setServerBaseUrl(submitted);
      _invalidateAfterBackendChange(ref);

      if (!context.mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Server URL updated')),
      );
    } on FormatException catch (e) {
      if (!context.mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.message)),
      );
    }
  }

  Future<void> _resetToDefault(BuildContext context, WidgetRef ref) async {
    await ref.read(serverBaseUrlProvider.notifier).setServerBaseUrl(
          ApiConstants.baseUrl,
        );
    _invalidateAfterBackendChange(ref);

    if (!context.mounted) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Reset to default URL')),
    );
  }

  void _invalidateAfterBackendChange(WidgetRef ref) {
    ref.invalidate(devicesListProvider);
    ref.invalidate(singleDeviceProvider);
    ref.invalidate(deviceShadowProvider);
    ref.invalidate(dashboardOverviewProvider);
    ref.invalidate(temperatureHistoryProvider);
  }
}
