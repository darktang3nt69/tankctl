import 'package:flutter/material.dart';
import 'package:tankctl_app/features/dashboard/widgets/dashboard_sorting.dart';

class DashboardListControls extends StatelessWidget {
  const DashboardListControls({
    super.key,
    required this.showOnlineOnly,
    required this.onToggleOnlineOnly,
    required this.sortMode,
    required this.onSortModeChanged,
  });

  final bool showOnlineOnly;
  final ValueChanged<bool> onToggleOnlineOnly;
  final DashboardSortMode sortMode;
  final ValueChanged<DashboardSortMode> onSortModeChanged;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Row(
      children: [
        Text(
          'MY TANKS',
          style: textTheme.labelSmall?.copyWith(
            color: Colors.white38,
            letterSpacing: 1.4,
            fontWeight: FontWeight.w600,
          ),
        ),
        const Spacer(),
        FilterChip(
          label: const Text('Online only'),
          selected: showOnlineOnly,
          onSelected: onToggleOnlineOnly,
          visualDensity: VisualDensity.compact,
        ),
        const SizedBox(width: 8),
        PopupMenuButton<DashboardSortMode>(
          tooltip: 'Sort tanks',
          onSelected: onSortModeChanged,
          itemBuilder: (context) => DashboardSortMode.values
              .map(
                (mode) => PopupMenuItem<DashboardSortMode>(
                  value: mode,
                  child: Row(
                    children: [
                      if (mode == sortMode)
                        const Icon(Icons.check_rounded, size: 16)
                      else
                        const SizedBox(width: 16),
                      const SizedBox(width: 8),
                      Text(sortLabel(mode)),
                    ],
                  ),
                ),
              )
              .toList(),
          child: Chip(
            visualDensity: VisualDensity.compact,
            avatar: const Icon(Icons.sort_rounded, size: 16),
            label: Text(sortLabel(sortMode)),
          ),
        ),
      ],
    );
  }
}
