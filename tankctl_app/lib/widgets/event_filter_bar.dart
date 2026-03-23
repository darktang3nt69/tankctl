/// Event filter bar widget - filter chips and controls
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/domain/event.dart';
import 'package:tankctl_app/providers/event_provider.dart';

class EventFilterBar extends ConsumerStatefulWidget {
  const EventFilterBar({super.key});

  @override
  ConsumerState<EventFilterBar> createState() => _EventFilterBarState();
}

class _EventFilterBarState extends ConsumerState<EventFilterBar> {
  bool _showAdvanced = false;
  late TextEditingController _searchController;

  @override
  void initState() {
    super.initState();
    _searchController = TextEditingController();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final filter = ref.watch(eventFilterProvider);
    final textTheme = Theme.of(context).textTheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Search field
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: TextField(
            controller: _searchController,
            onChanged: (value) {
              ref.read(eventFilterProvider.notifier).updateSearchQuery(
                    value.isEmpty ? null : value,
                  );
            },
            decoration: InputDecoration(
              hintText: 'Search events...',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: _searchController.text.isNotEmpty
                  ? IconButton(
                      icon: const Icon(Icons.clear),
                      onPressed: () {
                        _searchController.clear();
                        ref.read(eventFilterProvider.notifier).updateSearchQuery(null);
                      },
                    )
                  : null,
              isDense: true,
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
        ),

        // Quick filter chips
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Row(
            children: [
              // "All" chip
              SizedBox(
                height: 32,
                child: FilterChip(
                  label: const Text('All'),
                  selected: !filter.hasActiveFilters,
                  onSelected: (selected) {
                    if (selected) {
                      ref.read(eventFilterProvider.notifier).resetFilters();
                    }
                  },
                ),
              ),
              const SizedBox(width: 8),

              // Severity chips
              SizedBox(
                height: 32,
                child: FilterChip(
                  label: const Text('Critical'),
                  selected: filter.severity == EventSeverity.critical,
                  onSelected: (selected) {
                    ref.read(eventFilterProvider.notifier).updateSeverityFilter(
                          selected ? EventSeverity.critical : null,
                        );
                  },
                ),
              ),
              const SizedBox(width: 8),
              SizedBox(
                height: 32,
                child: FilterChip(
                  label: const Text('Warnings'),
                  selected: filter.severity == EventSeverity.warning,
                  onSelected: (selected) {
                    ref.read(eventFilterProvider.notifier).updateSeverityFilter(
                          selected ? EventSeverity.warning : null,
                        );
                  },
                ),
              ),
              const SizedBox(width: 8),

              // Category chips
              SizedBox(
                height: 32,
                child: FilterChip(
                  label: const Text('Light'),
                  selected: filter.category == EventCategory.light,
                  onSelected: (selected) {
                    ref.read(eventFilterProvider.notifier).updateCategoryFilter(
                          selected ? EventCategory.light : null,
                        );
                  },
                ),
              ),
              const SizedBox(width: 8),
              SizedBox(
                height: 32,
                child: FilterChip(
                  label: const Text('Temperature'),
                  selected: filter.category == EventCategory.temperature,
                  onSelected: (selected) {
                    ref.read(eventFilterProvider.notifier).updateCategoryFilter(
                          selected ? EventCategory.temperature : null,
                        );
                  },
                ),
              ),
              const SizedBox(width: 8),
              SizedBox(
                height: 32,
                child: FilterChip(
                  label: const Text('Offline'),
                  selected: filter.category == EventCategory.connectivity,
                  onSelected: (selected) {
                    ref.read(eventFilterProvider.notifier).updateCategoryFilter(
                          selected ? EventCategory.connectivity : null,
                        );
                  },
                ),
              ),
            ],
          ),
        ),

        // Active filters display
        if (filter.hasActiveFilters)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            child: Wrap(
              spacing: 4,
              children: [
                if (filter.severity != null)
                  Chip(
                    label: Text('Severity: ${filter.severity!.displayName}'),
                    onDeleted: () {
                      ref
                          .read(eventFilterProvider.notifier)
                          .updateSeverityFilter(null);
                    },
                    labelStyle: textTheme.labelSmall?.copyWith(fontSize: 10),
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                if (filter.category != null)
                  Chip(
                    label: Text('Type: ${filter.category!.displayName}'),
                    onDeleted: () {
                      ref
                          .read(eventFilterProvider.notifier)
                          .updateCategoryFilter(null);
                    },
                    labelStyle: textTheme.labelSmall?.copyWith(fontSize: 10),
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                if (filter.tankId != null)
                  Chip(
                    label: Text('Tank: ${filter.tankId}'),
                    onDeleted: () {
                      ref.read(eventFilterProvider.notifier).updateTankFilter(null);
                    },
                    labelStyle: textTheme.labelSmall?.copyWith(fontSize: 10),
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                TextButton(
                  onPressed: () {
                    ref.read(eventFilterProvider.notifier).resetFilters();
                  },
                  style: TextButton.styleFrom(
                    padding: EdgeInsets.zero,
                    minimumSize: const Size(60, 20),
                    tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                  child: const Text(
                    'Clear all',
                    style: TextStyle(fontSize: 11),
                  ),
                ),
              ],
            ),
          ),

        // Advanced filters toggle
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
          child: Row(
            children: [
              TextButton.icon(
                onPressed: () {
                  setState(() {
                    _showAdvanced = !_showAdvanced;
                  });
                },
                icon: Icon(
                  _showAdvanced
                      ? Icons.expand_less_rounded
                      : Icons.expand_more_rounded,
                  size: 18,
                ),
                label: const Text('More filters'),
                style: TextButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  minimumSize: Size.zero,
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
              ),
            ],
          ),
        ),

        // Advanced filters (hidden/collapsed by default)
        if (_showAdvanced)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Sort dropdown
                DropdownButton<String>(
                  value: filter.sortOrder,
                  items: const [
                    DropdownMenuItem(value: 'newest', child: Text('Newest first')),
                    DropdownMenuItem(value: 'oldest', child: Text('Oldest first')),
                    DropdownMenuItem(
                      value: 'severity',
                      child: Text('Severity (high to low)'),
                    ),
                  ],
                  onChanged: (value) {
                    if (value != null) {
                      ref
                          .read(eventFilterProvider.notifier)
                          .updateSortOrder(value);
                    }
                  },
                  isExpanded: true,
                  isDense: true,
                ),
                const SizedBox(height: 8),

                // Tank filter dropdown
                DropdownButton<String?>(
                  value: filter.tankId,
                  hint: const Text('Filter by Tank'),
                  items: const [
                    DropdownMenuItem(value: null, child: Text('All Tanks')),
                    DropdownMenuItem(value: 'tank1', child: Text('Tank 1')),
                    DropdownMenuItem(value: 'tank2', child: Text('Tank 2')),
                    DropdownMenuItem(value: 'tank3', child: Text('Tank 3')),
                  ],
                  onChanged: (value) {
                    ref.read(eventFilterProvider.notifier).updateTankFilter(value);
                  },
                  isExpanded: true,
                  isDense: true,
                ),
                const SizedBox(height: 8),

                // Event type filter dropdown
                DropdownButton<EventCategory?>(
                  value: filter.category,
                  hint: const Text('Filter by Event Type'),
                  items: [
                    const DropdownMenuItem(value: null, child: Text('All Events')),
                    DropdownMenuItem(
                      value: EventCategory.light,
                      child: Text('Light - ${EventCategory.light.displayName}'),
                    ),
                    DropdownMenuItem(
                      value: EventCategory.temperature,
                      child: Text('Temperature - ${EventCategory.temperature.displayName}'),
                    ),
                    DropdownMenuItem(
                      value: EventCategory.connectivity,
                      child: Text('Connectivity - ${EventCategory.connectivity.displayName}'),
                    ),
                    DropdownMenuItem(
                      value: EventCategory.system,
                      child: Text('System - ${EventCategory.system.displayName}'),
                    ),
                  ],
                  onChanged: (value) {
                    ref.read(eventFilterProvider.notifier).updateCategoryFilter(value);
                  },
                  isExpanded: true,
                  isDense: true,
                ),
              ],
            ),
          ),

        const Divider(height: 1, thickness: 0.5),
      ],
    );
  }
}
