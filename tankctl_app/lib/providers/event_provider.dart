/// Event providers for Riverpod state management
/// Handles event list, filtering, sorting, and real-time updates
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/api/api_client.dart';
import 'package:tankctl_app/domain/event.dart';
import 'package:tankctl_app/services/event_service.dart';

/// Event service dependency provider
final eventServiceProvider = Provider<EventService>((ref) {
  final dio = ref.watch(dioProvider);
  return EventService(dio);
});

/// Fetch events from backend (always fresh, no local cache)
/// Invalidate this to refetch after acknowledge/actions
final eventsProvider = FutureProvider.family<Map<String, dynamic>, ({
  int limit,
  int offset,
  String? tankId,
  EventCategory? category,
  EventSeverity? severity,
  DateTime? fromDate,
  DateTime? toDate,
  String sortOrder,
})>((ref, params) async {
  final eventService = ref.watch(eventServiceProvider);
  return eventService.getEvents(
    limit: params.limit,
    offset: params.offset,
    tankId: params.tankId,
    category: params.category,
    severity: params.severity,
    fromDate: params.fromDate,
    toDate: params.toDate,
    sortOrder: params.sortOrder,
  );
});

/// Filter state notifier — tracks active filters (ephemeral, in-memory only)
class EventFilterNotifier extends StateNotifier<EventFilter> {
  EventFilterNotifier() : super(const EventFilter());

  void setFilter(EventFilter filter) => state = filter;

  void updateTankFilter(String? tankId) {
    state = state.copyWith(
      tankId: tankId,
      clearTankId: tankId == null,
    );
  }

  void updateCategoryFilter(EventCategory? category) {
    state = state.copyWith(
      category: category,
      clearCategory: category == null,
    );
  }

  void updateSeverityFilter(EventSeverity? severity) {
    state = state.copyWith(
      severity: severity,
      clearSeverity: severity == null,
    );
  }

  void updateDateRange(DateTime? fromDate, DateTime? toDate) {
    state = state.copyWith(
      fromDate: fromDate,
      toDate: toDate,
      clearFromDate: fromDate == null,
      clearToDate: toDate == null,
    );
  }

  void updateSortOrder(String sortOrder) {
    state = state.copyWith(sortOrder: sortOrder);
  }

  void updateSearchQuery(String? query) {
    state = state.copyWith(
      searchQuery: query,
      clearSearchQuery: query == null,
    );
  }

  void resetFilters() {
    state = const EventFilter();
  }
}

/// Event filter provider
final eventFilterProvider =
    StateNotifierProvider<EventFilterNotifier, EventFilter>((ref) {
  return EventFilterNotifier();
});

/// Fetch filtered events based on current filter state
final filteredEventsProvider =
    FutureProvider<List<Event>>((ref) async {
  final filter = ref.watch(eventFilterProvider);

  // Fetch events with current filters
  final eventsData = await ref.watch(eventsProvider(
    (
      limit: 50,
      offset: 0,
      tankId: filter.tankId,
      category: filter.category,
      severity: filter.severity,
      fromDate: filter.fromDate,
      toDate: filter.toDate,
      sortOrder: filter.sortOrder,
    ),
  ).future);

  var events = (eventsData['events'] as List<Event>?) ?? [];

  // Apply search filter (client-side for now, could be backend)
  if (filter.searchQuery != null && filter.searchQuery!.isNotEmpty) {
    final query = filter.searchQuery!.toLowerCase();
    events = events
        .where((e) =>
            e.title.toLowerCase().contains(query) ||
            e.description.toLowerCase().contains(query) ||
            e.tankName.toLowerCase().contains(query) ||
            (e.deviceName?.toLowerCase().contains(query) ?? false))
        .toList();
  }

  return events;
});

/// Group events by date sections for timeline view (Phase 2)
final groupedEventsByDateProvider =
    FutureProvider<Map<String, List<Event>>>((ref) async {
  final events = await ref.watch(filteredEventsProvider.future);

  final grouped = <String, List<Event>>{};
  final now = DateTime.now();
  final today = DateTime(now.year, now.month, now.day);
  final yesterday = today.subtract(const Duration(days: 1));
  final weekAgo = today.subtract(const Duration(days: 7));

  for (final event in events) {
    final eventDate = DateTime(
      event.timestamp.year,
      event.timestamp.month,
      event.timestamp.day,
    );

    String groupKey;
    if (eventDate == today) {
      groupKey = 'Today';
    } else if (eventDate == yesterday) {
      groupKey = 'Yesterday';
    } else if (eventDate.isAfter(weekAgo)) {
      groupKey = 'Earlier this week';
    } else {
      groupKey = 'Older';
    }

    grouped.putIfAbsent(groupKey, () => []).add(event);
  }

  return grouped;
});

/// Deduplicated events (Phase 3) — collapses identical events within time window
final deduplicatedEventsProvider =
    FutureProvider<List<Event>>((ref) async {
  final events = await ref.watch(filteredEventsProvider.future);

  // Group events by (tank, category, type) within 10 seconds
  final dedupMap = <String, List<Event>>{};

  for (final event in events) {
    final key = '${event.tankId}|${event.category.name}|${event.type}';
    if (!dedupMap.containsKey(key)) {
      dedupMap[key] = [];
    }
    dedupMap[key]!.add(event);
  }

  // Flatten back; if group > 5, keep only first and a "group" marker
  // For now, just return original list; Phase 3 will enhance UI
  return events;
});

/// Unread events count (Phase 3)
final unreadEventCountProvider = FutureProvider<int>((ref) async {
  final events = await ref.watch(filteredEventsProvider.future);
  return events.where((e) => !e.isRead).length;
});

/// Mark event as read (Phase 3)
final markEventReadProvider =
    FutureProvider.family<void, String>((ref, eventId) async {
  final eventService = ref.watch(eventServiceProvider);
  await eventService.markEventRead(eventId);
  // Optionally invalidate depending on backend behavior
});
