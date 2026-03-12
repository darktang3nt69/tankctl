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
    final accentColor = Theme.of(context).colorScheme.primary;
    final onlineColor = showOnlineOnly ? accentColor : null;
    final hasCustomSort = sortMode != DashboardSortMode.alphabetical;
    final sortColor = hasCustomSort ? accentColor : null;

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
          avatar: Icon(
            showOnlineOnly ? Icons.check_rounded : Icons.filter_alt_outlined,
            size: 16,
            color: onlineColor,
          ),
          label: Text(
            'Online only',
            style: textTheme.labelLarge?.copyWith(
              color: onlineColor,
              fontWeight: showOnlineOnly ? FontWeight.w700 : FontWeight.w500,
            ),
          ),
          selected: showOnlineOnly,
          onSelected: onToggleOnlineOnly,
          visualDensity: VisualDensity.compact,
          selectedColor: accentColor.withValues(alpha: 0.15),
          side: showOnlineOnly
              ? BorderSide(color: accentColor.withValues(alpha: 0.5))
              : null,
          showCheckmark: false,
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
                      Icon(
                        mode == sortMode ? Icons.check_rounded : Icons.circle_outlined,
                        size: 16,
                        color: mode == sortMode
                            ? Theme.of(context).colorScheme.primary
                            : Colors.white38,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        sortLabel(mode),
                        style: textTheme.bodyMedium?.copyWith(
                          color: mode == sortMode
                              ? Theme.of(context).colorScheme.primary
                              : null,
                          fontWeight:
                              mode == sortMode ? FontWeight.w700 : FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
              )
              .toList(),
          child: Chip(
            visualDensity: VisualDensity.compact,
            backgroundColor:
                hasCustomSort ? sortColor?.withValues(alpha: 0.15) : null,
            side: hasCustomSort
                ? BorderSide(color: sortColor?.withValues(alpha: 0.5) ?? Colors.transparent)
                : null,
            avatar: Icon(
              Icons.sort_rounded,
              size: 16,
              color: sortColor,
            ),
            label: Text(
              sortLabel(sortMode),
              style: textTheme.labelLarge?.copyWith(
                color: sortColor,
                fontWeight: hasCustomSort ? FontWeight.w700 : FontWeight.w500,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
