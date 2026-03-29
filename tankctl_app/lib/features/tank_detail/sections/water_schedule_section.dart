import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/domain/device_detail.dart';
import 'package:tankctl_app/providers/device_detail_provider.dart';
import 'package:tankctl_app/providers/water_schedule_provider.dart';
import 'package:tankctl_app/widgets/day_of_week_selector.dart';
import 'package:tankctl_app/widgets/time_selector.dart';

// Clean version - all broken duplicates removed during Phase5 cleanup

/// Water schedule section with inline add/edit form and schedule list.
///
/// Features:
/// - Expandable section header with add button
/// - Inline form that toggles visibility
/// - Multi-select days for weekly schedules
/// - Single date picker for custom dates
/// - Time selector with validation
/// - Per-schedule notification preferences
/// - Edit/delete actions for existing schedules
/// - Loading and error states
/// - Full Riverpod state management integration
class WaterScheduleSection extends ConsumerStatefulWidget {
  final String deviceId;

  const WaterScheduleSection({
    super.key,
    required this.deviceId,
  });

  @override
  ConsumerState<WaterScheduleSection> createState() =>
      _WaterScheduleSectionState();
}

class _WaterScheduleSectionState extends ConsumerState<WaterScheduleSection> {
  bool _isExpanded = true;
  bool _showForm = false;
  late TextEditingController _notesController;
  bool _isSaving = false;

  static const List<String> _dayNames = [
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
    _notesController = TextEditingController();
  }

  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }

  /// Start editing a schedule
  void _startEdit(WaterSchedule schedule) {
    ref.read(waterScheduleFormProvider.notifier).startEditing(schedule);
    setState(() {
      _showForm = true;
      _notesController.text = schedule.notes ?? '';
    });
  }

  /// Reset form to initial state
  void _resetForm() {
    ref.read(waterScheduleFormProvider.notifier).resetForm();
    setState(() {
      _showForm = false;
      _notesController.clear();
      _isSaving = false;
    });
  }

  /// Validate form state using provider
  String? _validateForm() {
    return ref.read(waterScheduleFormProvider.notifier).validate();
  }

  /// Save schedule (create or update)
  Future<void> _saveSchedule() async {
    final validation = _validateForm();
    if (validation != null) {
      _showSnackBar(validation, success: false);
      return;
    }

    final formNotifier = ref.read(waterScheduleFormProvider.notifier);
    final isEditing = ref.read(waterScheduleFormProvider).isEditing;
    final notes = _notesController.text.trim();

    formNotifier.updateNotes(notes.isNotEmpty ? notes : null);

    setState(() => _isSaving = true);

    try {
      if (isEditing) {
        // Update existing
        await ref
            .read(updateWaterScheduleProvider(widget.deviceId).future);
        _showSnackBar('Schedule updated', success: true);
        ref.invalidate(waterSchedulesProvider(widget.deviceId));
        _resetForm();
      } else {
        // Create new
        await ref
            .read(createWaterScheduleProvider(widget.deviceId).future);
        _showSnackBar('Schedule created', success: true);
        ref.invalidate(waterSchedulesProvider(widget.deviceId));
        _resetForm();
      }
    } catch (e) {
      _showSnackBar('Failed to save: $e', success: false);
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  /// Delete schedule with confirmation
  Future<void> _deleteSchedule(WaterSchedule schedule) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete Schedule'),
        content: const Text('Are you sure you want to delete this water schedule?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    try {
      await ref.read(
        deleteWaterScheduleProvider(
          (deviceId: widget.deviceId, scheduleId: schedule.id),
        ).future,
      );
      _showSnackBar('Schedule deleted', success: true);
      ref.invalidate(waterSchedulesProvider(widget.deviceId));
    } catch (e) {
      _showSnackBar('Failed to delete: $e', success: false);
    }
  }

  /// Show snackbar message
  void _showSnackBar(String message, {required bool success}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(
              success ? Icons.check_circle : Icons.error_outline,
              color: Colors.white,
            ),
            const SizedBox(width: 12),
            Expanded(child: Text(message)),
          ],
        ),
        backgroundColor: success ? Colors.green : Colors.red,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  /// Format days list to display string
  String _formatDays(List<int> days) {
    if (days.isEmpty) return '';
    return days.map((d) => _dayNames[d]).join(', ');
  }

  @override
  Widget build(BuildContext context) {
    final schedulesAsync = ref.watch(waterSchedulesProvider(widget.deviceId));
    final formState = ref.watch(waterScheduleFormProvider);

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header with expand/collapse
          GestureDetector(
            onTap: () => setState(() => _isExpanded = !_isExpanded),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Icon(
                      _isExpanded ? Icons.expand_less : Icons.expand_more,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'Water Schedules',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                  ],
                ),
                TextButton(
                  onPressed: () {
                    if (_showForm) {
                      _resetForm();
                    } else {
                      ref.read(waterScheduleFormProvider.notifier).resetForm();
                      setState(() => _showForm = true);
                    }
                  },
                  child: Text(_showForm ? '✕ Cancel' : '+ Add Schedule'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          if (!_isExpanded)
            const SizedBox.shrink()
          else ...[
            // Inline form if visible
            if (_showForm) ...[
              _buildInlineForm(context, formState),
              const SizedBox(height: 24),
            ],
            // Schedules list
            schedulesAsync.when(
              loading: () => const Center(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: CircularProgressIndicator(),
                ),
              ),
              error: (error, _) =>
                  _buildEmptyState(context, 'Failed to load schedules'),
              data: (schedules) => schedules.isEmpty && !_showForm
                  ? _buildEmptyState(context, 'No water schedules')
                  : ListView.separated(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: schedules.length,
                      separatorBuilder: (_, _) => const SizedBox(height: 8),
                      itemBuilder: (_, i) =>
                          _buildScheduleCard(context, schedules[i]),
                    ),
            ),
          ],
        ],
      ),
    );
  }

  /// Build inline form
  Widget _buildInlineForm(
    BuildContext context,
    WaterScheduleFormState formState,
  ) {
    final formNotifier = ref.read(waterScheduleFormProvider.notifier);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            formState.isEditing ? 'Edit Schedule' : 'New Schedule',
            style: Theme.of(context).textTheme.labelLarge,
          ),
          const SizedBox(height: 16),

          // Schedule type selector
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(
                value: 'weekly',
                label: Text('Weekly'),
                icon: Icon(Icons.repeat),
              ),
              ButtonSegment(
                value: 'custom',
                label: Text('Custom'),
                icon: Icon(Icons.calendar_today),
              ),
            ],
            selected: {formState.scheduleType},
            onSelectionChanged: (v) =>
                formNotifier.updateScheduleType(v.first),
          ),
          const SizedBox(height: 20),

          // Weekly days selector
          if (formState.scheduleType == 'weekly') ...[
            DayOfWeekSelector(
              selectedDays: formState.selectedDays,
              onSelectionChanged: (days) =>
                  formNotifier.updateSelectedDays(days),
              label: 'Days of Week',
              showDayNames: true,
            ),
            const SizedBox(height: 20),
          ],

          // Custom date picker
          if (formState.scheduleType == 'custom') ...[
            Text('Date', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            Container(
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey.withValues(alpha: 0.3)),
                borderRadius: BorderRadius.circular(8),
              ),
              child: TextButton.icon(
                onPressed: () async {
                  final picked = await showDatePicker(
                    context: context,
                    initialDate: formState.selectedDate != null
                        ? DateTime.parse(formState.selectedDate!)
                        : DateTime.now(),
                    firstDate: DateTime.now(),
                    lastDate: DateTime.now().add(const Duration(days: 365)),
                  );
                  if (picked != null) {
                    formNotifier.updateDate(
                      '${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}',
                    );
                  }
                },
                icon: const Icon(Icons.calendar_today),
                label: Text(
                  formState.selectedDate ?? 'Select Date',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ),
            ),
            const SizedBox(height: 20),
          ],

          // Time selector
          TimeSelector(
            initialTime: formState.selectedTime,
            onTimeChanged: (time) => formNotifier.updateTime(time),
            label: 'Time',
            showSpinners: true,
            spinnerIncrement: 15,
          ),
          const SizedBox(height: 20),

          // Notification toggles
          Text('Notifications', style: Theme.of(context).textTheme.labelLarge),
          const SizedBox(height: 8),
          ..._buildNotificationToggles(context, formState, formNotifier),
          const SizedBox(height: 20),

          // Notes field
          TextField(
            controller: _notesController,
            decoration: InputDecoration(
              hintText: 'Notes (optional)',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
              ),
              contentPadding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            ),
            maxLines: 2,
          ),
          const SizedBox(height: 20),

          // Action buttons
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton(
                onPressed: _isSaving ? null : _resetForm,
                child: const Text('Cancel'),
              ),
              const SizedBox(width: 12),
              ElevatedButton(
                onPressed: _isSaving ? null : _saveSchedule,
                child: _isSaving
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Text(formState.isEditing ? 'Update' : 'Add'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Build notification toggles
  List<Widget> _buildNotificationToggles(
    BuildContext context,
    WaterScheduleFormState formState,
    WaterScheduleFormNotifier formNotifier,
  ) {
    return [
      _buildToggleRow(
        context,
        'Notify 24h before',
        formState.notify24h,
        (v) => formNotifier.toggleNotify24h(v),
      ),
      const SizedBox(height: 8),
      _buildToggleRow(
        context,
        'Notify 1h before',
        formState.notify1h,
        (v) => formNotifier.toggleNotify1h(v),
      ),
      const SizedBox(height: 8),
      _buildToggleRow(
        context,
        'Notify at time',
        formState.notifyOnTime,
        (v) => formNotifier.toggleNotifyOnTime(v),
      ),
    ];
  }

  /// Build a single toggle row
  Widget _buildToggleRow(
    BuildContext context,
    String label,
    bool value,
    ValueChanged<bool> onChanged,
  ) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: Theme.of(context).textTheme.bodyMedium),
        Switch(value: value, onChanged: onChanged),
      ],
    );
  }

  /// Build schedule card
  Widget _buildScheduleCard(BuildContext context, WaterSchedule schedule) {
    final displayInfo = schedule.scheduleType == 'weekly'
        ? _formatDays(schedule.daysOfWeek)
        : (schedule.scheduleDate ?? 'Unknown');

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.grey.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey.withValues(alpha: 0.2)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  schedule.displayType,
                  style: Theme.of(context)
                      .textTheme
                      .bodySmall
                      ?.copyWith(color: Colors.grey),
                ),
                const SizedBox(height: 2),
                Text(
                  displayInfo,
                  style: Theme.of(context)
                      .textTheme
                      .bodyMedium
                      ?.copyWith(fontWeight: FontWeight.bold),
                ),
                Text(
                  schedule.scheduleTime,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                if (schedule.notes?.isNotEmpty == true)
                  Text(
                    schedule.notes!,
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
          IconButton(
            icon: const Icon(Icons.edit_outlined, size: 20),
            onPressed: () => _startEdit(schedule),
            tooltip: 'Edit schedule',
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline, size: 20),
            onPressed: () => _deleteSchedule(schedule),
            tooltip: 'Delete schedule',
          ),
        ],
      ),
    );
  }

  /// Build empty state
  Widget _buildEmptyState(BuildContext context, String message) {
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
}
