import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/domain/device_detail.dart';
import 'package:tankctl_app/providers/device_detail_provider.dart';

/// Light schedule section with enabled toggle and time editing
class LightScheduleSection extends ConsumerStatefulWidget {
  final DeviceDetail device;
  final String deviceId;

  const LightScheduleSection({
    super.key,
    required this.device,
    required this.deviceId,
  });

  @override
  ConsumerState<LightScheduleSection> createState() =>
      _LightScheduleSectionState();
}

class _LightScheduleSectionState extends ConsumerState<LightScheduleSection> {
  late String _startTime;
  late String _endTime;

  @override
  void initState() {
    super.initState();
    _startTime = widget.device.lightSchedule?.startTime ?? '08:00';
    _endTime = widget.device.lightSchedule?.endTime ?? '20:00';
  }

  @override
  void didUpdateWidget(LightScheduleSection oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.device.lightSchedule != widget.device.lightSchedule) {
      _startTime = widget.device.lightSchedule?.startTime ?? '08:00';
      _endTime = widget.device.lightSchedule?.endTime ?? '20:00';
    }
  }

  Future<void> _selectTime(BuildContext context, bool isStartTime) async {
    final TimeOfDay? picked = await showTimePicker(
      context: context,
      initialTime: TimeOfDay(
        hour: int.parse((isStartTime ? _startTime : _endTime).split(':')[0]),
        minute: int.parse((isStartTime ? _startTime : _endTime).split(':')[1]),
      ),
    );

    if (picked != null) {
      setState(() {
        final timeStr =
            '${picked.hour.toString().padLeft(2, '0')}:${picked.minute.toString().padLeft(2, '0')}';
        if (isStartTime) {
          _startTime = timeStr;
        } else {
          _endTime = timeStr;
        }
      });
    }
  }

  Future<void> _updateSchedule() async {
    final schedule = widget.device.lightSchedule;
    if (schedule == null) return;

    try {
      final service = ref.read(deviceDetailServiceProvider);
      await service.setLightSchedule(
        widget.deviceId,
        startTime: _startTime,
        endTime: _endTime,
        enabled: schedule.enabled,
      );

      // Refresh the device detail data
      ref.invalidate(deviceDetailProvider(widget.deviceId));

      if (mounted) {
        ScaffoldMessenger.of(context).clearSnackBars();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Row(
              children: [
                Icon(Icons.check_circle, color: Colors.white),
                SizedBox(width: 12),
                Text('Light schedule updated'),
              ],
            ),
            backgroundColor: Colors.green,
            duration: const Duration(seconds: 2),
            behavior: SnackBarBehavior.floating,
            margin: const EdgeInsets.all(16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).clearSnackBars();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.error, color: Colors.white),
                const SizedBox(width: 12),
                Expanded(child: Text('Failed to update: $e')),
              ],
            ),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 3),
            behavior: SnackBarBehavior.floating,
            margin: const EdgeInsets.all(16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final schedule = widget.device.lightSchedule;
    // Use local state provider for immediate UI feedback
    final enabledState = ref.watch(lightScheduleEnabledProvider(widget.deviceId));
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
                // Enabled toggle
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Enabled',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    Switch(
                      value: displayEnabled,
                      onChanged: (newValue) async {
                        if (schedule != null) {
                          try {
                            // Optimistically update UI immediately
                            ref
                                .read(lightScheduleEnabledProvider(
                                    widget.deviceId).notifier)
                                .state = newValue;

                            // Call the API to update the schedule
                            final service =
                                ref.read(deviceDetailServiceProvider);
                            await service.setLightSchedule(
                              widget.deviceId,
                              startTime: _startTime,
                              endTime: _endTime,
                              enabled: newValue,
                            );
                            // Refresh the device detail data
                            ref.invalidate(
                                deviceDetailProvider(widget.deviceId));
                          } catch (e) {
                            // Revert on error
                            ref
                                .read(lightScheduleEnabledProvider(
                                    widget.deviceId).notifier)
                                .state = schedule.enabled;

                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text('Failed to update: $e'),
                                ),
                              );
                            }
                          }
                        }
                      },
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                // Time picker row
                Row(
                  children: [
                    Expanded(
                      child: _buildTimePickerButton(
                        context,
                        'Start',
                        _startTime,
                        true,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _buildTimePickerButton(
                        context,
                        'End',
                        _endTime,
                        false,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                // Update button
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: _updateSchedule,
                    icon: const Icon(Icons.save),
                    label: const Text('Update Schedule'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTimePickerButton(
    BuildContext context,
    String label,
    String time,
    bool isStart,
  ) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final accentColor = isStart ? Colors.amber : Colors.orange;
    
    return Material(
      child: InkWell(
        onTap: () => _selectTime(context, isStart),
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                accentColor.withValues(alpha: 0.12),
                accentColor.withValues(alpha: 0.06),
              ],
            ),
            border: Border.all(
              color: accentColor.withValues(alpha: 0.3),
              width: 1.5,
            ),
            boxShadow: [
              BoxShadow(
                color: accentColor.withValues(alpha: 0.1),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    isStart ? Icons.light_mode : Icons.dark_mode,
                    size: 16,
                    color: accentColor,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    label,
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: accentColor,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                time,
                style: Theme.of(context).textTheme.displaySmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  fontSize: 28,
                  color: isDark ? Colors.white : Colors.black87,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
