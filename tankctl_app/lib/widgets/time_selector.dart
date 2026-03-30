import 'package:flutter/material.dart';

/// A tappable time-picker chip.
///
/// Shows the current time in HH:MM format and opens the system time-picker
/// dialog when tapped. No spinners, no text input — clean one-tap experience.
///
/// All existing call-sites keep working because the public API
/// (initialTime, onTimeChanged, label, readOnly) is preserved.
/// The now-unused [showSpinners] and [spinnerIncrement] parameters are kept
/// as no-ops so nothing breaks.
class TimeSelector extends StatefulWidget {
  /// Current time in HH:MM format (e.g. "14:30").
  final String initialTime;

  /// Fires whenever the user picks a new time, with the HH:MM string.
  final ValueChanged<String> onTimeChanged;

  /// Optional label shown above the chip.
  final String? label;

  /// When true the chip is non-interactive.
  final bool readOnly;

  /// Kept for backwards-compat — no longer has any effect.
  final bool showSpinners;

  /// Kept for backwards-compat — no longer has any effect.
  final int spinnerIncrement;

  const TimeSelector({
    super.key,
    required this.initialTime,
    required this.onTimeChanged,
    this.label,
    this.readOnly = false,
    this.showSpinners = true,
    this.spinnerIncrement = 15,
  });

  @override
  State<TimeSelector> createState() => _TimeSelectorState();
}

class _TimeSelectorState extends State<TimeSelector> {
  late String _time;

  @override
  void initState() {
    super.initState();
    _time = _normalise(widget.initialTime);
  }

  @override
  void didUpdateWidget(TimeSelector oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialTime != widget.initialTime) {
      setState(() => _time = _normalise(widget.initialTime));
    }
  }

  /// Accept HH:MM or HH:MM:SS; always return HH:MM.
  static String _normalise(String raw) {
    if (raw.length == 8 && raw[5] == ':') return raw.substring(0, 5);
    return raw;
  }

  Future<void> _pick() async {
    if (widget.readOnly) return;
    final parts = _time.split(':');
    final h = int.tryParse(parts[0]) ?? 0;
    final m = int.tryParse(parts.length > 1 ? parts[1] : '0') ?? 0;

    final picked = await showTimePicker(
      context: context,
      initialTime: TimeOfDay(hour: h, minute: m),
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(context).copyWith(alwaysUse24HourFormat: true),
        child: child!,
      ),
    );

    if (picked != null) {
      final newTime =
          '${picked.hour.toString().padLeft(2, '0')}:${picked.minute.toString().padLeft(2, '0')}';
      setState(() => _time = newTime);
      widget.onTimeChanged(newTime);
    }
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final textTheme = Theme.of(context).textTheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (widget.label != null) ...[
          Text(widget.label!, style: textTheme.labelLarge),
          const SizedBox(height: 8),
        ],
        InkWell(
          onTap: widget.readOnly ? null : _pick,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: widget.readOnly
                    ? colorScheme.outline.withValues(alpha: 0.25)
                    : colorScheme.outline.withValues(alpha: 0.6),
              ),
              color: colorScheme.surfaceContainerHighest
                  .withValues(alpha: widget.readOnly ? 0.3 : 0.5),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.schedule_rounded,
                  size: 18,
                  color: widget.readOnly
                      ? colorScheme.onSurface.withValues(alpha: 0.35)
                      : colorScheme.primary,
                ),
                const SizedBox(width: 10),
                Text(
                  _time,
                  style: textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w700,
                    letterSpacing: 2,
                    color: widget.readOnly
                        ? colorScheme.onSurface.withValues(alpha: 0.4)
                        : colorScheme.onSurface,
                  ),
                ),
                if (!widget.readOnly) ...[
                  const SizedBox(width: 10),
                  Icon(
                    Icons.edit_rounded,
                    size: 14,
                    color: colorScheme.onSurface.withValues(alpha: 0.45),
                  ),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }
}
