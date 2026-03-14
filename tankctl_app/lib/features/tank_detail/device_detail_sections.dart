/// Device detail screen sections
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/domain/device_detail.dart';
import 'package:tankctl_app/providers/device_detail_provider.dart';

/// Health metrics section (WiFi, uptime, last seen)
class HealthMetricsSection extends StatelessWidget {
  final DeviceDetail device;

  const HealthMetricsSection({super.key, required this.device});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Health Metrics',
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
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildMetric(context, 'WiFi', '${device.rssi ?? 0}%'),
                _buildMetric(context, 'Uptime', _formatUptime(device.uptimeMs ?? 0)),
                _buildMetric(context, 'Status', device.status.toUpperCase()),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetric(BuildContext context, String label, String value) {
    return Column(
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Colors.grey,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }

  String _formatUptime(int uptimeMs) {
    final duration = Duration(milliseconds: uptimeMs);
    final days = duration.inDays;
    final hours = duration.inHours % 24;
    final minutes = duration.inMinutes % 60;
    
    if (days > 0) {
      return '${days}d ${hours}h';
    } else if (hours > 0) {
      return '${hours}h ${minutes}m';
    } else {
      return '${minutes}m';
    }
  }
}

/// Temperature section with graph and threshold sliders
class TemperatureSection extends ConsumerWidget {
  final DeviceDetail device;
  final String deviceId;

  const TemperatureSection({
    super.key,
    required this.device,
    required this.deviceId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Temperature',
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
                // Placeholder for temperature chart
                Container(
                  height: 200,
                  decoration: BoxDecoration(
                    color: Colors.grey.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Center(
                    child: Text('Temperature Chart (Last 24h)'),
                  ),
                ),
                const SizedBox(height: 16),
                // Min threshold
                Text(
                  'Min Threshold: ${device.tempThresholdLow ?? '—'}°C',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                if (device.tempThresholdLow != null)
                  Slider(
                    value: device.tempThresholdLow!,
                    min: 0,
                    max: 50,
                    onChanged: (_) {},
                  ),
                const SizedBox(height: 12),
                // Max threshold
                Text(
                  'Max Threshold: ${device.tempThresholdHigh ?? '—'}°C',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                if (device.tempThresholdHigh != null)
                  Slider(
                    value: device.tempThresholdHigh!,
                    min: 0,
                    max: 50,
                    onChanged: (_) {},
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Light schedule section
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
                      value: schedule?.enabled ?? true,
                      onChanged: (_) {},
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

/// Water changes section
class WaterChangesSection extends ConsumerWidget {
  final String deviceId;

  const WaterChangesSection({super.key, required this.deviceId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final schedulesAsync = ref.watch(waterSchedulesProvider(deviceId));

    return schedulesAsync.when(
      loading: () => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Water Changes',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            const Center(child: CircularProgressIndicator()),
          ],
        ),
      ),
      error: (_, _) => const SizedBox.shrink(),
      data: (schedules) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Water Changes',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                TextButton(
                  onPressed: () => _showAddScheduleModal(context, ref),
                  child: const Text('+ Add'),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (schedules.isEmpty)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.grey.withValues(alpha: 0.05),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Center(
                  child: Text(
                    'No water changes scheduled',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.grey,
                    ),
                  ),
                ),
              )
            else
              ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: schedules.length,
                itemBuilder: (context, index) {
                  final schedule = schedules[index];
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.grey.withValues(alpha: 0.05),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                schedule.displayType,
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: Colors.grey,
                                ),
                              ),
                              if (schedule.scheduleType == 'weekly')
                                Text(
                                  schedule.dayName ?? '',
                                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    fontWeight: FontWeight.bold,
                                  ),
                                )
                              else
                                Text(
                                  schedule.scheduleDate ?? '',
                                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              Text(
                                schedule.scheduleTime,
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                            ],
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete_outline),
                            onPressed: () {
                              // Delete water schedule
                            },
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
          ],
        ),
      ),
    );
  }

  void _showAddScheduleModal(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => AddWaterScheduleModal(deviceId: deviceId),
    );
  }
}

/// Device info section (read-only)
class DeviceInfoSection extends StatelessWidget {
  final DeviceDetail device;

  const DeviceInfoSection({super.key, required this.device});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Device Info',
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
                _buildInfoRow(context, 'Device ID', device.deviceId),
                const Divider(),
                _buildInfoRow(context, 'Firmware', device.firmwareVersion ?? '—'),
                const Divider(),
                _buildInfoRow(context, 'Connection', device.status),
                const Divider(),
                _buildInfoRow(context, 'RSSI', '${device.rssi ?? 0} dBm'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(BuildContext context, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Colors.grey,
            ),
          ),
          Text(
            value,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}

/// Device settings modal for editing metadata
class DeviceSettingsModal extends ConsumerWidget {
  final DeviceDetail device;
  final String deviceId;

  const DeviceSettingsModal({
    super.key,
    required this.device,
    required this.deviceId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Container(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        top: 16,
        left: 16,
        right: 16,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Edit Device Settings',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 24),
            TextField(
              decoration: InputDecoration(
                labelText: 'Device Name',
                hintText: device.deviceName ?? device.deviceId,
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              decoration: InputDecoration(
                labelText: 'Location',
                hintText: device.location,
              ),
            ),
            const SizedBox(height: 16),
            // Icon selector
            DropdownButtonFormField(
              decoration: const InputDecoration(labelText: 'Icon'),
              initialValue: device.iconType,
              items: [
                'fish_bowl',
                'tropical',
                'planted_tank',
                'saltwater',
                'reef',
                'ponds',
                'betta',
                'aquascape',
              ]
                  .map((icon) => DropdownMenuItem(
                value: icon,
                child: Text(icon),
              ))
                  .toList(),
              onChanged: (_) {},
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Save'),
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

/// Modal for adding water change schedule
class AddWaterScheduleModal extends ConsumerWidget {
  final String deviceId;

  const AddWaterScheduleModal({super.key, required this.deviceId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Container(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        top: 16,
        left: 16,
        right: 16,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Schedule Water Change',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 24),
            // Schedule type selector
            StatefulBuilder(
              builder: (context, setState) {
                String selectedType = 'weekly';
                return RadioGroup<String>(
                  groupValue: selectedType,
                  onChanged: (v) => setState(() => selectedType = v!),
                  child: Row(
                    children: [
                      Expanded(
                        child: RadioListTile<String>(
                          title: const Text('Weekly'),
                          value: 'weekly',
                        ),
                      ),
                      Expanded(
                        child: RadioListTile<String>(
                          title: const Text('Custom'),
                          value: 'custom',
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Add'),
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}
