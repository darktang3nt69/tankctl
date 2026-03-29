import 'package:flutter/material.dart';

/// Inline time selector widget with tap-to-edit and up/down buttons.
///
/// Displays time in HH:MM format with optional spinner buttons for quick
/// increments/decrements. Tapping the time field opens a time picker dialog.
///
/// Validates time format (00:00-23:59) and provides continuous feedback.
class TimeSelector extends StatefulWidget {
  /// Initial time in HH:MM format (e.g., "14:30").
  final String initialTime;

  /// Callback: fires when time changes with new HH:MM string.
  final ValueChanged<String> onTimeChanged;

  /// Optional label to display above the time input.
  final String? label;

  /// Allow spinner buttons for +/- minute adjustments.
  /// Defaults to true.
  final bool showSpinners;

  /// Minutes to increment/decrement on spinner click.
  /// Defaults to 15 minutes.
  final int spinnerIncrement;

  /// If true, input is disabled and appears read-only.
  /// Defaults to false.
  final bool readOnly;

  const TimeSelector({
    super.key,
    required this.initialTime,
    required this.onTimeChanged,
    this.label,
    this.showSpinners = true,
    this.spinnerIncrement = 15,
    this.readOnly = false,
  });

  @override
  State<TimeSelector> createState() => _TimeSelectorState();
}

class _TimeSelectorState extends State<TimeSelector> {
  late TextEditingController _controller;
  String? _errorText;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.initialTime);
    _validateTime(widget.initialTime);
  }

  @override
  void didUpdateWidget(TimeSelector oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialTime != widget.initialTime) {
      _controller.text = widget.initialTime;
      _validateTime(widget.initialTime);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  /// Validate time format HH:MM (00:00 - 23:59).
  bool _validateTime(String time) {
    final regex = RegExp(r'^([01]\d|2[0-3]):([0-5]\d)$');
    final isValid = regex.hasMatch(time);

    setState(() {
      _errorText = isValid ? null : 'Invalid time format (HH:MM)';
    });

    return isValid;
  }

  /// Parse HH:MM string into hour and minute integers.
  List<int> _parseTime(String time) {
    try {
      final parts = time.split(':');
      return [int.parse(parts[0]), int.parse(parts[1])];
    } catch (_) {
      return [0, 0];
    }
  }

  /// Format hour and minute into HH:MM string.
  String _formatTime(int hour, int minute) {
    return '${hour.toString().padLeft(2, '0')}:${minute.toString().padLeft(2, '0')}';
  }

  /// Clamp hour to 0-23 and minute to 0-59.
  void _updateTime(int hour, int minute) {
    final h = hour.clamp(0, 23);
    final m = minute.clamp(0, 59);
    final newTime = _formatTime(h, m);

    if (newTime != _controller.text) {
      setState(() => _controller.text = newTime);
      if (_validateTime(newTime)) {
        widget.onTimeChanged(newTime);
      }
    }
  }

  /// Open time picker dialog.
  Future<void> _showTimePicker() async {
    if (widget.readOnly) return;

    final [hour, minute] = _parseTime(_controller.text);

    final picked = await showTimePicker(
      context: context,
      initialTime: TimeOfDay(hour: hour, minute: minute),
    );

    if (picked != null) {
      final newTime = _formatTime(picked.hour, picked.minute);
      setState(() => _controller.text = newTime);
      if (_validateTime(newTime)) {
        widget.onTimeChanged(newTime);
      }
    }
  }

  /// Increment or decrement time by spinner amount.
  void _updateBySpinner(int minuteDelta) {
    final [hour, minute] = _parseTime(_controller.text);
    final totalMinutes = hour * 60 + minute + minuteDelta;

    // Wrap around day boundary
    final wrappedMinutes = totalMinutes < 0
        ? totalMinutes + (24 * 60)
        : totalMinutes % (24 * 60);

    final newHour = wrappedMinutes ~/ 60;
    final newMinute = wrappedMinutes % 60;

    _updateTime(newHour, newMinute);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (widget.label != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text(
              widget.label!,
              style: Theme.of(context).textTheme.labelLarge,
            ),
          ),
        Row(
          children: [
            // Decrement button
            if (widget.showSpinners && !widget.readOnly)
              SizedBox(
                width: 40,
                height: 40,
                child: IconButton(
                  icon: const Icon(Icons.remove),
                  onPressed: () =>
                      _updateBySpinner(-widget.spinnerIncrement),
                  tooltip: 'Decrease time',
                  iconSize: 18,
                ),
              ),

            // Time input field
            Expanded(
              child: GestureDetector(
                onTap: widget.readOnly ? null : _showTimePicker,
                child: TextField(
                  controller: _controller,
                  readOnly: true,
                  enabled: !widget.readOnly,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    letterSpacing: 2,
                  ),
                  decoration: InputDecoration(
                    hintText: 'HH:MM',
                    errorText: _errorText,
                    filled: true,
                    fillColor: widget.readOnly
                        ? Colors.grey.withValues(alpha: 0.1)
                        : Colors.transparent,
                    prefixIcon: const Icon(Icons.schedule),
                    suffixIcon: _errorText == null
                        ? const Icon(Icons.check_circle,
                            color: Colors.green)
                        : const Icon(Icons.error, color: Colors.red),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                    errorBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: const BorderSide(color: Colors.red),
                    ),
                  ),
                ),
              ),
            ),

            // Increment button
            if (widget.showSpinners && !widget.readOnly)
              SizedBox(
                width: 40,
                height: 40,
                child: IconButton(
                  icon: const Icon(Icons.add),
                  onPressed: () =>
                      _updateBySpinner(widget.spinnerIncrement),
                  tooltip: 'Increase time',
                  iconSize: 18,
                ),
              ),
          ],
        ),
      ],
    );
  }
}
