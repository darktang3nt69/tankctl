import 'package:flutter/material.dart';
import 'package:tankctl_app/features/dashboard/widgets/settings/backend_settings_card.dart';
import 'package:tankctl_app/features/dashboard/widgets/settings/live_updates_settings_card.dart';
import 'package:tankctl_app/features/dashboard/widgets/settings/notifications_settings_card.dart';
import 'package:tankctl_app/features/dashboard/widgets/settings/settings_section_header.dart';
import 'package:tankctl_app/features/dashboard/widgets/settings/update_settings_card.dart';

class SettingsTab extends StatelessWidget {
  const SettingsTab({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const SettingsSectionHeader(
          title: 'Backend',
          subtitle:
              'Set the server URL used by both REST and live WebSocket connections.',
        ),
        const SizedBox(height: 20),
        const BackendSettingsCard(),
        const SizedBox(height: 24),
        const SettingsSectionHeader(
          title: 'Notifications',
          subtitle: 'Control which alerts can interrupt you.',
        ),
        const SizedBox(height: 20),
        const NotificationsSettingsCard(),
        const SizedBox(height: 24),
        const SettingsSectionHeader(
          title: 'Live Updates',
          subtitle:
              'WebSocket events apply immediately. This interval forces a background resync so the dashboard stays current within a few seconds even if an event is missed.',
        ),
        const SizedBox(height: 20),
        const LiveUpdatesSettingsCard(),
        const SizedBox(height: 24),
        const SettingsSectionHeader(
          title: 'App Update',
          subtitle:
              'Check for new versions from GitHub. Updates are downloaded and installed directly in the app.',
        ),
        const SizedBox(height: 20),
        const UpdateSettingsCard(),
        const SizedBox(height: 24),
      ],
    );
  }
}
