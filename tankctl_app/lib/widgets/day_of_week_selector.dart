import 'package:flutter/material.dart';

/// Multi-select day-of-week picker widget with Material 3 styling.
///
/// Displays 7 checkboxes in a 4-column grid layout (3 rows) for selecting
/// combination of days. Days are 0-indexed (0=Sunday, 6=Saturday).
///
/// Callback fires whenever selection changes, providing updated list of
/// selected day indices.
class DayOfWeekSelector extends StatefulWidget {
  /// Selected day indices (0=Sun, 1=Mon, ..., 6=Sat).
  final List<int> selectedDays;

  /// Callback: fires when selection changes with new list of selected days.
  final ValueChanged<List<int>> onSelectionChanged;

  /// Optional label to display above grid.
  final String? label;

  /// Whether to show day names ('Sun', 'Mon', etc.) above grid.
  /// Defaults to true.
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

  static const List<String> _dayNames = [
    'Sun',
    'Mon',
    'Tue',
    'Wed',
    'Thu',
    'Fri',
    'Sat'
  ];

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

  void _toggleDay(int day) {
    setState(() {
      if (_selected.contains(day)) {
        _selected.remove(day);
      } else {
        _selected.add(day);
      }
    });
    widget.onSelectionChanged(_selected.toList()..sort());
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (widget.label != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Text(
              widget.label!,
              style: Theme.of(context).textTheme.labelLarge,
            ),
          ),
        GridView.count(
          crossAxisCount: 4,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: 8,
          crossAxisSpacing: 8,
          childAspectRatio: 1,
          children: List.generate(7, (index) {
            return _DayCheckbox(
              day: index,
              dayName: _dayNames[index],
              selected: _selected.contains(index),
              onChanged: (_) => _toggleDay(index),
            );
          }),
        ),
      ],
    );
  }
}

/// Single day checkbox cell for day-of-week selector.
class _DayCheckbox extends StatelessWidget {
  final int day;
  final String dayName;
  final bool selected;
  final ValueChanged<bool> onChanged;

  const _DayCheckbox({
    required this.day,
    required this.dayName,
    required this.selected,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => onChanged(!selected),
        borderRadius: BorderRadius.circular(8),
        child: Container(
          decoration: BoxDecoration(
            border: Border.all(
              color: selected
                  ? Theme.of(context).primaryColor
                  : Colors.grey.withValues(alpha: 0.3),
              width: selected ? 2 : 1,
            ),
            borderRadius: BorderRadius.circular(8),
            color: selected
                ? Theme.of(context).primaryColor.withValues(alpha: 0.1)
                : Colors.transparent,
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Checkbox(
                value: selected,
                onChanged: (value) => onChanged(value ?? false),
                visualDensity: VisualDensity.compact,
              ),
              Text(
                dayName,
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  fontWeight: selected ? FontWeight.bold : FontWeight.normal,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
