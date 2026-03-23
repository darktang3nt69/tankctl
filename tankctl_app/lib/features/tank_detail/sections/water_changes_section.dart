import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/domain/device_detail.dart';
import 'package:tankctl_app/providers/device_detail_provider.dart';

/// Water changes section — lists water change schedules with notification toggles.
class WaterChangesSection extends ConsumerWidget {
  final String deviceId;

  const WaterChangesSection({super.key, required this.deviceId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final schedulesAsync = ref.watch(waterSchedulesProvider(deviceId));

    return schedulesAsync.when(
      loading: () => _scaffold(
        context,
        header: _header(context, ref, enabled: false),
        body: const Center(child: CircularProgressIndicator()),
      ),
      error: (_, _) => _scaffold(
        context,
        header: _header(context, ref, enabled: false),
        body: _emptyLabel(context, 'Failed to load schedules'),
      ),
      data: (schedules) => _scaffold(
        context,
        header: _header(context, ref, enabled: true),
        body: schedules.isEmpty
            ? _emptyLabel(context, 'No water changes scheduled')
            : ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: schedules.length,
                itemBuilder: (_, i) => _ScheduleCard(
                  key: ValueKey(schedules[i].id),
                  schedule: schedules[i],
                  deviceId: deviceId,
                  onRefresh: () =>
                      ref.invalidate(waterSchedulesProvider(deviceId)),
                ),
              ),
      ),
    );
  }

  Widget _scaffold(BuildContext context,
      {required Widget header, required Widget body}) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [header, const SizedBox(height: 12), body],
      ),
    );
  }

  Widget _header(BuildContext context, WidgetRef ref, {required bool enabled}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          'Water Changes',
          style: Theme.of(context)
              .textTheme
              .titleMedium
              ?.copyWith(fontWeight: FontWeight.bold),
        ),
        TextButton(
          onPressed: enabled
              ? () => _showAddModal(context, ref)
              : null,
          child: const Text('+ Add'),
        ),
      ],
    );
  }

  Widget _emptyLabel(BuildContext context, String message) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Center(
        child: Text(
          message,
          style: Theme.of(context)
              .textTheme
              .bodySmall
              ?.copyWith(color: Colors.grey),
        ),
      ),
    );
  }

  void _showAddModal(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => AddWaterScheduleModal(
        deviceId: deviceId,
        onSaved: () => ref.invalidate(waterSchedulesProvider(deviceId)),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Schedule card with notification toggle + delete
// ---------------------------------------------------------------------------

class _ScheduleCard extends ConsumerStatefulWidget {
  final WaterSchedule schedule;
  final String deviceId;
  final VoidCallback onRefresh;

  const _ScheduleCard({
    super.key,
    required this.schedule,
    required this.deviceId,
    required this.onRefresh,
  });

  @override
  ConsumerState<_ScheduleCard> createState() => _ScheduleCardState();
}

class _ScheduleCardState extends ConsumerState<_ScheduleCard> {
  late bool _enabled;
  bool _toggling = false;

  @override
  void initState() {
    super.initState();
    _enabled = widget.schedule.enabled;
  }

  @override
  void didUpdateWidget(_ScheduleCard old) {
    super.didUpdateWidget(old);
    if (old.schedule.enabled != widget.schedule.enabled) {
      _enabled = widget.schedule.enabled;
    }
  }

  Future<void> _toggleEnabled() async {
    if (_toggling) return;
    final next = !_enabled;
    setState(() {
      _toggling = true;
      _enabled = next;
    });
    try {
      final svc = ref.read(deviceDetailServiceProvider);
      await svc.updateWaterSchedule(widget.deviceId, widget.schedule,
          enabled: next);
      _toast(next ? 'Notifications enabled' : 'Notifications disabled',
          success: true);
      widget.onRefresh();
    } catch (_) {
      setState(() => _enabled = !next); // rollback
      _toast('Failed to update notifications', success: false);
    } finally {
      if (mounted) setState(() => _toggling = false);
    }
  }

  Future<void> _delete() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete Schedule'),
        content:
            const Text('Are you sure you want to delete this water schedule?'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) return;

    try {
      final svc = ref.read(deviceDetailServiceProvider);
      await svc.deleteWaterSchedule(widget.deviceId, widget.schedule.id);
      widget.onRefresh();
    } catch (_) {
      if (mounted) _toast('Failed to delete schedule', success: false);
    }
  }

  void _toast(String message, {required bool success}) {
    if (!mounted) return;
    final overlay = Overlay.of(context);
    late OverlayEntry entry;
    entry = OverlayEntry(
      builder: (_) => Positioned(
        bottom: 80,
        left: 24,
        right: 24,
        child: Material(
          color: Colors.transparent,
          child: Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: success ? Colors.green[700] : Colors.red[700],
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Icon(
                  success ? Icons.check_circle : Icons.error_outline,
                  color: Colors.white,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(message,
                      style: const TextStyle(color: Colors.white)),
                ),
              ],
            ),
          ),
        ),
      ),
    );
    overlay.insert(entry);
    Future.delayed(const Duration(seconds: 2), entry.remove);
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.schedule;
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: Colors.grey.withValues(alpha: 0.05),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    s.displayType,
                    style: Theme.of(context)
                        .textTheme
                        .bodySmall
                        ?.copyWith(color: Colors.grey),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    s.scheduleType == 'weekly'
                        ? (s.dayNames ?? '')
                        : (s.scheduleDate ?? ''),
                    style: Theme.of(context)
                        .textTheme
                        .bodyMedium
                        ?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  Text(
                    s.scheduleTime,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  if (s.notes?.isNotEmpty == true)
                    Text(
                      s.notes!,
                      style: Theme.of(context)
                          .textTheme
                          .bodySmall
                          ?.copyWith(color: Colors.grey),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                ],
              ),
            ),
            // Notification toggle
            if (_toggling)
              const SizedBox(
                width: 40,
                child: Center(
                  child: SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                ),
              )
            else
              IconButton(
                icon: Icon(
                  _enabled
                      ? Icons.notifications_active
                      : Icons.notifications_off_outlined,
                  color: _enabled ? Colors.green : Colors.grey,
                  size: 20,
                ),
                tooltip: _enabled
                    ? 'Disable notifications'
                    : 'Enable notifications',
                onPressed: _toggleEnabled,
              ),
            // Delete
            IconButton(
              icon: const Icon(Icons.delete_outline, size: 20),
              onPressed: _delete,
            ),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Add water schedule bottom-sheet modal
// ---------------------------------------------------------------------------

class AddWaterScheduleModal extends ConsumerStatefulWidget {
  final String deviceId;
  final VoidCallback onSaved;

  const AddWaterScheduleModal({
    super.key,
    required this.deviceId,
    required this.onSaved,
  });

  @override
  ConsumerState<AddWaterScheduleModal> createState() =>
      _AddWaterScheduleModalState();
}

class _AddWaterScheduleModalState
    extends ConsumerState<AddWaterScheduleModal> {
  String _scheduleType = 'weekly';
  late Set<int> _daysOfWeek;
  String? _scheduleDate;
  String _scheduleTime = '12:00';
  bool _enabled = true;
  bool _saving = false;

  late final TextEditingController _notesCtrl;

  static const _dayNames = [
    'Sunday',
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday'
  ];

  @override
  void initState() {
    super.initState();
    _daysOfWeek = {1}; // Default to Monday
    _notesCtrl = TextEditingController();
  }

  @override
  void dispose() {
    _notesCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickTime() async {
    final parts = _scheduleTime.split(':');
    final picked = await showTimePicker(
      context: context,
      initialTime: TimeOfDay(
        hour: int.parse(parts[0]),
        minute: int.parse(parts[1]),
      ),
    );
    if (picked != null && mounted) {
      setState(() {
        _scheduleTime =
            '${picked.hour.toString().padLeft(2, '0')}:${picked.minute.toString().padLeft(2, '0')}';
      });
    }
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null && mounted) {
      setState(() {
        _scheduleDate =
            '${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}';
      });
    }
  }

  Future<void> _save() async {
    if (_scheduleType == 'custom' && _scheduleDate == null) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please select a date')));
      return;
    }
    if (_scheduleType == 'weekly' && _daysOfWeek.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please select at least one day')));
      return;
    }

    setState(() => _saving = true);
    try {
      final svc = ref.read(deviceDetailServiceProvider);
      await svc.createWaterSchedule(
        widget.deviceId,
        scheduleType: _scheduleType,
        daysOfWeek: _scheduleType == 'weekly' ? _daysOfWeek.toList() : null,
        scheduleDate: _scheduleType == 'custom' ? _scheduleDate : null,
        scheduleTime: _scheduleTime,
        notes:
            _notesCtrl.text.trim().isEmpty ? null : _notesCtrl.text.trim(),
        enabled: _enabled,
      );
      widget.onSaved();
      if (mounted) Navigator.pop(context);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Failed to save: $e')));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
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
              style: Theme.of(context)
                  .textTheme
                  .titleLarge
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 20),

            // Schedule type
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(
                  value: 'weekly',
                  label: Text('Weekly'),
                  icon: Icon(Icons.repeat),
                ),
                ButtonSegment(
                  value: 'custom',
                  label: Text('Custom Date'),
                  icon: Icon(Icons.calendar_today),
                ),
              ],
              selected: {_scheduleType},
              onSelectionChanged: (v) =>
                  setState(() => _scheduleType = v.first),
            ),
            const SizedBox(height: 20),

            // Days of week (weekly multi-select)
            if (_scheduleType == 'weekly') ...[
              Text('Days of Week',
                  style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                children: List.generate(
                  7,
                  (i) => FilterChip(
                    label: Text(_dayNames[i].substring(0, 3)),
                    selected: _daysOfWeek.contains(i),
                    onSelected: (selected) {
                      setState(() {
                        if (selected) {
                          _daysOfWeek.add(i);
                        } else {
                          _daysOfWeek.remove(i);
                        }
                      });
                    },
                  ),
                ),
              ),
              const SizedBox(height: 16),
            ],

            // Custom date
            if (_scheduleType == 'custom') ...[
              Text('Date', style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: _pickDate,
                icon: const Icon(Icons.calendar_today),
                label: Text(_scheduleDate ?? 'Select Date'),
              ),
              const SizedBox(height: 16),
            ],

            // Time
            Text('Time (IST)',
                style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: _pickTime,
              icon: const Icon(Icons.access_time),
              label: Text(_scheduleTime),
            ),
            const SizedBox(height: 16),

            // Notes
            Text('Notes (optional)',
                style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            TextField(
              controller: _notesCtrl,
              decoration: const InputDecoration(
                hintText: 'e.g. 30% water change',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),

            // Notifications toggle
            SwitchListTile(
              value: _enabled,
              onChanged: (v) => setState(() => _enabled = v),
              title: const Text('Send notifications'),
              subtitle: const Text(
                  'Reminders 24 h, 1 h before and at the scheduled time'),
              contentPadding: EdgeInsets.zero,
            ),
            const SizedBox(height: 16),

            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _saving ? null : _save,
                child: _saving
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('Add Schedule'),
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

