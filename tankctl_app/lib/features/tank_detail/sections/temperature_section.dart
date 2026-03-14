import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/domain/device_detail.dart';
import 'package:tankctl_app/providers/telemetry_provider.dart';

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
    final tempHistoryAsync = ref.watch(temperatureHistoryProvider(deviceId));

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
                // Temperature chart or empty state
                _buildTemperatureChart(context, tempHistoryAsync),
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

  Widget _buildTemperatureChart(
    BuildContext context,
    AsyncValue<List<double>> tempHistoryAsync,
  ) {
    return tempHistoryAsync.when(
      loading: () => Container(
        height: 200,
        decoration: BoxDecoration(
          color: Colors.grey.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(8),
        ),
        child: const Center(
          child: SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ),
      ),
      error: (_, __) => Container(
        height: 200,
        decoration: BoxDecoration(
          color: Colors.grey.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Center(
          child: Text(
            'No temperature data',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Colors.grey,
            ),
          ),
        ),
      ),
      data: (tempHistory) {
        if (tempHistory.isEmpty) {
          return Container(
            height: 200,
            decoration: BoxDecoration(
              color: Colors.grey.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Center(
              child: Text(
                'No temperature data available',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.grey,
                ),
              ),
            ),
          );
        }
        return Container(
          height: 200,
          decoration: BoxDecoration(
            color: Colors.grey.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Center(
            child: Text(
              'Temperature Chart (Last 24h)\n${tempHistory.length} readings',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
        );
      },
    );
  }
}
