import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/domain/device_detail.dart';

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
