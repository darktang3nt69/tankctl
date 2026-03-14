import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/domain/device_detail.dart';
import 'package:tankctl_app/providers/device_detail_provider.dart';

/// Light schedule section with enabled toggle
class LightScheduleSection extends ConsumerWidget {
  final DeviceDetail device;
  final String deviceId;

  const LightScheduleSection({
    super.key,
    required this.device,
    required this.deviceId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final schedule = device.lightSchedule;
    // Use local state provider for immediate UI feedback
    final enabledState = ref.watch(lightScheduleEnabledProvider(deviceId));
    final displayEnabled = enabledState ?? schedule?.enabled ?? true;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Light Schedule',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey.withValues(alpha: 0.05),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.grey.withValues(alpha: 0.2)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Enabled'),
                    Switch(
                      value: displayEnabled,
                      onChanged: (newValue) async {
                        if (schedule != null) {
                          try {
                            // Optimistically update UI immediately
                            ref
                                .read(
                                    lightScheduleEnabledProvider(deviceId).notifier)
                                .state = newValue;

                            // Call the API to update the schedule
                            final service =
                                ref.read(deviceDetailServiceProvider);
                            await service.setLightSchedule(
                              deviceId,
                              startTime: schedule.startTime,
                              endTime: schedule.endTime,
                              enabled: newValue,
                            );
                            // Refresh the device detail data to reflect the toggle change
                            ref.invalidate(deviceDetailProvider(deviceId));
                          } catch (e) {
                            // Revert on error
                            ref
                                .read(
                                    lightScheduleEnabledProvider(deviceId).notifier)
                                .state = schedule.enabled;

                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                    content: Text(
                                        'Failed to update schedule: $e')),
                              );
                            }
                          }
                        }
                      },
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  'Start: ${schedule?.startTime ?? '08:00'}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                Text(
                  'End: ${schedule?.endTime ?? '20:00'}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
