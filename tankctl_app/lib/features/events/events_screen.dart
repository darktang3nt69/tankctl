/// Events screen - main tab showing event list with filters
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/domain/event.dart';
import 'package:tankctl_app/features/events/event_details_sheet.dart';
import 'package:tankctl_app/providers/event_provider.dart';
import 'package:tankctl_app/widgets/event_filter_bar.dart';
import 'package:tankctl_app/widgets/event_timeline.dart';

class EventsScreen extends ConsumerStatefulWidget {
  const EventsScreen({super.key});

  @override
  ConsumerState<EventsScreen> createState() => _EventsScreenState();
}

class _EventsScreenState extends ConsumerState<EventsScreen> {
  late ScrollController _scrollController;

  @override
  void initState() {
    super.initState();
    _scrollController = ScrollController();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Events'),
        centerTitle: false,
        elevation: 0,
        backgroundColor: Colors.transparent,
      ),
      body: Column(
        children: [
          // Filter bar
          const EventFilterBar(),

          // Event list (grouped by date)
          Expanded(
            child: ref.watch(groupedEventsByDateProvider).when(
                  loading: () => _buildLoadingState(),
                  error: (error, stack) => _buildErrorState(error, context),
                  data: (groupedEvents) {
                    if (groupedEvents.isEmpty) {
                      return _buildEmptyState(context);
                    }

                    return RefreshIndicator(
                      onRefresh: () async {
                        // Refresh the events by invalidating the provider
                        ref.invalidate(groupedEventsByDateProvider);
                        // Wait for the new data to load
                        await ref
                            .read(groupedEventsByDateProvider.future)
                            .catchError((_) => <String, List<Event>>{});
                      },
                      child: EventTimeline(
                        groupedEvents: groupedEvents,
                        onEventTap: (event) {
                          _showEventDetails(context, event);
                        },
                      ),
                    );
                  },
                ),
          ),
        ],
      ),
    );
  }

  /// Loading state widget
  Widget _buildLoadingState() {
    return ListView.builder(
      itemCount: 5,
      itemBuilder: (context, index) => Container(
        margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        height: 120,
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.05),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Shimmer.fromColors(
          baseColor: Colors.white.withValues(alpha: 0.1),
          highlightColor: Colors.white.withValues(alpha: 0.2),
          child: Container(
            color: Colors.white.withValues(alpha: 0.05),
          ),
        ),
      ),
    );
  }

  /// Empty state widget
  Widget _buildEmptyState(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.inbox_outlined,
            size: 64,
            color: Colors.white38,
          ),
          const SizedBox(height: 16),
          Text(
            'No events yet',
            style: textTheme.titleMedium?.copyWith(
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Device activity and alerts will appear here',
            style: textTheme.bodySmall?.copyWith(
              color: Colors.white54,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          TextButton(
            onPressed: () {
              ref.read(eventFilterProvider.notifier).resetFilters();
            },
            child: const Text('Clear filters'),
          ),
        ],
      ),
    );
  }

  /// Error state widget
  Widget _buildErrorState(Object error, BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.error_outline_rounded,
            size: 64,
            color: Colors.white38,
          ),
          const SizedBox(height: 16),
          Text(
            'Couldn\'t load events',
            style: textTheme.titleMedium?.copyWith(
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            error.toString(),
            style: textTheme.bodySmall?.copyWith(
              color: Colors.white54,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () {
              ref.invalidate(filteredEventsProvider);
            },
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  /// Show event detail sheet (Phase 2)
  void _showEventDetails(BuildContext context, Event event) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => EventDetailsSheet(
        event: event,
      ),
    );
  }
}

/// Shimmer effect for loading state
class Shimmer extends StatefulWidget {
  final Widget child;
  final Color baseColor;
  final Color highlightColor;
  final Duration duration;

  const Shimmer.fromColors({
    required this.child,
    required this.baseColor,
    required this.highlightColor,
    this.duration = const Duration(milliseconds: 1500),
    super.key,
  });

  @override
  State<Shimmer> createState() => _ShimmerState();
}

class _ShimmerState extends State<Shimmer> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: widget.duration,
      vsync: this,
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return ShaderMask(
          blendMode: BlendMode.lighten,
          shaderCallback: (bounds) {
            final progress = _controller.value;
            return LinearGradient(
              begin: Alignment(-1 - progress * 2, 0),
              end: Alignment(1 + progress * 2, 0),
              colors: [
                widget.baseColor,
                widget.highlightColor,
                widget.baseColor,
              ],
              stops: [0, 0.5, 1],
            ).createShader(bounds);
          },
          child: child,
        );
      },
      child: widget.child,
    );
  }
}
