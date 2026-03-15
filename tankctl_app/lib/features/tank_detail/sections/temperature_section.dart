import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/domain/device_detail.dart';
import 'package:tankctl_app/domain/time_range.dart';
import 'package:tankctl_app/providers/telemetry_provider.dart';
import 'package:tankctl_app/services/telemetry_service.dart';
import 'package:tankctl_app/widgets/temperature_mini_chart.dart';

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
    final tempHistoryAsync = ref.watch(
      temperatureHistoryWithTimeProvider(deviceId),
    );
    final selectedTimeRange = ref.watch(temperatureTimeRangeProvider(deviceId));

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Temperature',
                style: Theme.of(
                  context,
                ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
              ),
              // Time range selector buttons
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    for (final range in TimeRange.common)
                      Padding(
                        padding: const EdgeInsets.only(left: 6),
                        child: _buildTimeRangeButton(
                          context,
                          ref,
                          range,
                          isSelected: range == selectedTimeRange,
                        ),
                      ),
                  ],
                ),
              ),
            ],
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
                // Temperature chart
                _buildTemperatureChart(context, tempHistoryAsync),
                const SizedBox(height: 12),
                // Threshold chips row
                Row(
                  children: [
                    _buildThresholdChip(
                      context,
                      label: 'Min',
                      value: device.tempThresholdLow,
                      color: Colors.blue,
                    ),
                    const SizedBox(width: 8),
                    _buildThresholdChip(
                      context,
                      label: 'Max',
                      value: device.tempThresholdHigh,
                      color: Colors.orange,
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _getTimeRangeLabel(List<DateTime> timestamps) {
    if (timestamps.isEmpty) return 'No data';
    if (timestamps.length == 1) return 'Latest';
    final oldest = timestamps.first;
    final newest = timestamps.last;
    final diff = newest.difference(oldest);
    if (diff.inDays > 0) return 'Last ${diff.inDays}d';
    if (diff.inHours > 0) return 'Last ${diff.inHours}h';
    return 'Last ${diff.inMinutes}m';
  }

  Widget _buildTemperatureChart(
    BuildContext context,
    AsyncValue<List<TelemetryReading>> tempHistoryAsync,
  ) {
    return tempHistoryAsync.when(
      loading: () => Container(
        height: 180,
        decoration: BoxDecoration(
          color: Colors.grey.withValues(alpha: 0.08),
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
      error: (_, _) => _emptyChart(context, 'No temperature data'),
      data: (readings) {
        final valid = readings.where((r) => r.value != 0).toList();
        if (valid.isEmpty) return _emptyChart(context, 'Awaiting readings…');

        final points = valid.map((r) => r.value).toList();
        final timestamps = valid
            .map((r) => r.time)
            .whereType<DateTime>()
            .toList();
        final timeRange = _getTimeRangeLabel(timestamps);

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  timeRange,
                  style: Theme.of(
                    context,
                  ).textTheme.labelSmall?.copyWith(color: Colors.white38),
                ),
                Text(
                  '${points.length} readings',
                  style: Theme.of(
                    context,
                  ).textTheme.labelSmall?.copyWith(color: Colors.white38),
                ),
              ],
            ),
            const SizedBox(height: 8),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.grey.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(8),
                ),
                constraints: BoxConstraints(
                  minWidth: MediaQuery.of(context).size.width - 48,
                ),
                child: TemperatureMiniChart(
                  data: points,
                  height: 200,
                  showAxes: true,
                  timestamps: timestamps.isEmpty ? null : timestamps,
                  thresholdHigh: device.tempThresholdHigh,
                  thresholdLow: device.tempThresholdLow,
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _emptyChart(BuildContext context, String message) {
    return Container(
      height: 180,
      decoration: BoxDecoration(
        color: Colors.grey.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Center(
        child: Text(
          message,
          style: Theme.of(
            context,
          ).textTheme.bodySmall?.copyWith(color: Colors.grey),
        ),
      ),
    );
  }

  Widget _buildThresholdChip(
    BuildContext context, {
    required String label,
    required double? value,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withValues(alpha: 0.25)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '$label: ',
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: color.withValues(alpha: 0.8),
            ),
          ),
          Text(
            value != null ? '${value.toStringAsFixed(1)}°C' : 'Not set',
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: value != null ? Colors.white70 : Colors.white30,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTimeRangeButton(
    BuildContext context,
    WidgetRef ref,
    TimeRange range, {
    required bool isSelected,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () {
          ref.read(temperatureTimeRangeProvider(deviceId).notifier).state =
              range;
        },
        borderRadius: BorderRadius.circular(6),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            color: isSelected
                ? Colors.blue.withValues(alpha: 0.3)
                : Colors.grey.withValues(alpha: 0.08),
            borderRadius: BorderRadius.circular(6),
            border: Border.all(
              color: isSelected
                  ? Colors.blue.withValues(alpha: 0.6)
                  : Colors.grey.withValues(alpha: 0.2),
            ),
          ),
          child: Text(
            range.label,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: isSelected ? Colors.blue[300] : Colors.white60,
              fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
            ),
          ),
        ),
      ),
    );
  }
}
