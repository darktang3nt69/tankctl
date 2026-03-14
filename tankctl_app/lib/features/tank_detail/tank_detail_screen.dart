import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/domain/device_detail.dart';
import 'package:tankctl_app/providers/device_detail_provider.dart';
import 'package:tankctl_app/providers/event_provider.dart';
import 'package:tankctl_app/widgets/event_card.dart';
import 'device_detail_sections.dart';

/// Device detail screen showing all settings in one scrollable view
class TankDetailScreen extends ConsumerWidget {
  const TankDetailScreen({super.key, required this.deviceId});

  final String deviceId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final deviceAsync = ref.watch(deviceDetailProvider(deviceId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Device Detail'),
        centerTitle: false,
        elevation: 0,
      ),
      body: deviceAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, st) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error, size: 64, color: Colors.red),
              const SizedBox(height: 16),
              const Text('Failed to load device detail'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.refresh(deviceDetailProvider(deviceId)),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (device) => _buildContent(context, ref, device),
      ),
    );
  }

  Widget _buildContent(BuildContext context, WidgetRef ref, DeviceDetail device) {
    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Tank Header with Health Metrics (Combined)
            TankHeaderWithHealthSection(device: device),
            const SizedBox(height: 24),

            // Temperature Graph & Thresholds
            TemperatureSection(device: device, deviceId: deviceId),
            const SizedBox(height: 24),

            // Light Schedule
            LightScheduleSection(device: device, deviceId: deviceId),
            const SizedBox(height: 24),

            // Water Changes
            WaterChangesSection(deviceId: deviceId),
            const SizedBox(height: 24),

            // Recent Events Section
            RecentEventsSection(deviceId: deviceId),
            const SizedBox(height: 24),

            // Device Info (Read-only)
            DeviceInfoSection(device: device),
            const SizedBox(height: 24),

            // Edit Settings Button
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => _showSettingsModal(context, ref, device),
                  child: const Text('Edit Settings'),
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  void _showSettingsModal(BuildContext context, WidgetRef ref, DeviceDetail device) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (context) => DeviceSettingsModal(
        device: device,
        deviceId: deviceId,
      ),
    );
  }


}

/// Recent events for this device
class RecentEventsSection extends ConsumerWidget {
  final String deviceId;

  const RecentEventsSection({super.key, required this.deviceId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Filter events for this device
    final eventsAsync = ref.watch(filteredEventsProvider);

    return eventsAsync.when(
      loading: () => const SizedBox.shrink(),
      error: (_, _) => const SizedBox.shrink(),
      data: (allEvents) {
        final deviceEvents = allEvents.take(3).toList();

        if (deviceEvents.isEmpty) {
          return const SizedBox.shrink();
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Recent Events',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  TextButton(
                    onPressed: () {
                      // Navigate to events screen filtered by this device
                      Navigator.of(context).pushNamed(
                        '/events',
                        arguments: {'deviceId': deviceId},
                      );
                    },
                    child: const Text('View All'),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: deviceEvents.length,
              itemBuilder: (context, index) {
                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  child: EventCard(
                    event: deviceEvents[index],
                    onTap: () {},
                  ),
                );
              },
            ),
          ],
        );
      },
    );
  }
}
