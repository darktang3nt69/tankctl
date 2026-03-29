import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../domain/event.dart';

// Note: To enable real-time features, add 'web_socket_channel' to pubspec.yaml
// and uncomment the import above. WebSocket implementation requires backend support.

/// Real-time event streaming via WebSocket
/// Prepends new events to the list as they arrive
// Placeholder implementation - requires web_socket_channel package
class RealtimeEventNotifier extends StateNotifier<List<Event>> {
  final String wsUrl; // e.g., 'ws://localhost:8000/events/stream'

  RealtimeEventNotifier(this.wsUrl) : super([]) {
    // WebSocket connection setup deferred - requires web_socket_channel package
    // _connectWebSocket();
  }

  // Placeholder for WebSocket connection
  // Uncomment when web_socket_channel is added as a dependency
  /*
  void _connectWebSocket() {
    try {
      final channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      channel.stream.listen(
        (message) {
          try {
            final json = jsonDecode(message);
            final event = TankEvent.fromJson(json);
            state = [event, ...state];
          } catch (e) {
            // Log error
          }
        },
        onError: (error) {
          _isConnected = false;
          Future.delayed(const Duration(seconds: 5), _connectWebSocket);
        },
        onDone: () {
          _isConnected = false;
          Future.delayed(const Duration(seconds: 5), _connectWebSocket);
        },
      );
      _isConnected = true;
    } catch (e) {
      _isConnected = false;
    }
  }
  */

  void addEvent(Event event) {
    try {
      state = [event, ...state];
    } catch (e) {
      // Silently handle state mutation on disposed providers
    }
  }

  void replaceAll(List<Event> events) {
    try {
      state = events;
    } catch (e) {
      // Silently handle state mutation on disposed providers
    }
  }

  void close() {
    // Cleanup
  }

  @override
  void dispose() {
    close();
    super.dispose();
  }
}

// Real-time events provider (requires backend WebSocket support)
final realtimeEventProvider = StateNotifierProvider<
    RealtimeEventNotifier,
    List<Event>>((ref) {
  // Configure your WebSocket URL here
  const wsUrl = 'ws://localhost:8000/events/stream'; // Replace with actual URL
  final notifier = RealtimeEventNotifier(wsUrl);
  ref.onDispose(() => notifier.close());
  return notifier;
});


