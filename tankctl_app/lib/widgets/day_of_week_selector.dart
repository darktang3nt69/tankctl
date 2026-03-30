import 'package:flutter/material.dart';

/// Multi-select day-of-week picker rendered as a row of circular pill chips.
///
/// Days are 0-indexed (0=Sunday, 6=Saturday). Displayed Mon → Sun.
/// Callback fires whenever selection changes with the updated sorted list.
class DayOfWeekSelector extends StatefulWidget {
  /// Selected day indices (0=Sun, 1=Mon, …, 6=Sat).
  final List<int> selectedDays;

  /// Fires when selection changes with the new sorted list of day indices.
  final ValueChanged<List<int>> onSelectionChanged;

  /// Optional label displayed above the row.
  final String? label;

  /// Kept for API compatibility – ignored in the new design.
  final bool showDayNames;

  const DayOfWeekSelector({
    super.key,
    required this.selectedDays,
    required this.onSelectionChanged,
    this.label,
    this.showDayNames = true,
  });

  @override
  State<DayOfWeekSelector> createState() => _DayOfWeekSelectorState();
}

class _DayOfWeekSelectorState extends State<DayOfWeekSelector> {
  late Set<int> _selected;

  // Display order: Monday first. Index maps to 0-based day (Sun=0).
  static const _order = [1, 2, 3, 4, 5, 6, 0];
  static const _labels = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];

  @override
  void initState() {
    super.initState();
    _selected = Set<int>.from(widget.selectedDays);
  }

  @override
  void didUpdateWidget(DayOfWeekSelector oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.selectedDays != widget.selectedDays) {
      _selected = Set<int>.from(widget.selectedDays);
    }
  }

  void _toggle(int dayIndex) {
    setState(() {
      if (_selected.contains(dayIndex)) {
        _selected.remove(dayIndex);
      } else {
        _selected.add(dayIndex);
      }
    });
    widget.onSelectionChanged(_selected.toList()..sort());
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (widget.label != null) ...[
          Text(widget.label!, style: Theme.of(context).textTheme.labelLarge),
          const SizedBox(height: 10),
        ],
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: List.generate(7, (i) {
            final dayIndex = _order[i];
            final selected = _selected.contains(dayIndex);
            return _DayPill(
              label: _labels[i],
              selected: selected,
              onTap: () => _toggle(dayIndex),
              colorScheme: colorScheme,
            );
          }),
        ),
      ],
    );
  }
}

class _DayPill extends StatelessWidget {
  const _DayPill({
    required this.label,
    required this.selected,
    required this.onTap,
    required this.colorScheme,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;
  final ColorScheme colorScheme;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        width: 38,
        height: 38,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: selected ? colorScheme.primary : Colors.transparent,
          border: Border.all(
            color: selected
                ? colorScheme.primary
                : colorScheme.outline.withValues(alpha: 0.45),
            width: 1.5,
          ),
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: selected ? FontWeight.w700 : FontWeight.w400,
              color: selected
                  ? colorScheme.onPrimary
                  : colorScheme.onSurfaceVariant,
            ),
          ),
        ),
      ),
    );
  }
}
