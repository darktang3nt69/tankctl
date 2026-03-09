import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/api/api_constants.dart';

class WebSocketService {
  WebSocketService();

  final _controller = StreamController<Map<String, dynamic>>.broadcast();

  WebSocket? _socket;
  Timer? _reconnectTimer;
  bool _disposed = false;
  bool _connecting = false;
  int _reconnectAttempt = 0;

  Stream<Map<String, dynamic>> get stream => _controller.stream;

  Future<void> connect() async {
    if (_disposed || _connecting || _socket != null) {
      return;
    }

    _connecting = true;

    try {
      final socket = await WebSocket.connect(_buildUri().toString());
      socket.pingInterval = const Duration(seconds: 20);
      _socket = socket;
      _reconnectAttempt = 0;

      socket.listen(
        _handleMessage,
        onError: (_) => _scheduleReconnect(),
        onDone: _scheduleReconnect,
        cancelOnError: true,
      );
    } finally {
      _connecting = false;
    }
  }

  void _handleMessage(dynamic message) {
    if (message is! String) {
      return;
    }

    final decoded = jsonDecode(message);
    if (decoded is Map<String, dynamic>) {
      _controller.add(decoded);
    }
  }

  void _scheduleReconnect() {
    _socket = null;
    if (_disposed) {
      return;
    }

    _reconnectTimer?.cancel();
    _reconnectAttempt += 1;
    final seconds = _reconnectAttempt.clamp(1, 5);
    _reconnectTimer = Timer(Duration(seconds: seconds), () {
      unawaited(connect());
    });
  }

  Uri _buildUri() {
    final baseUri = Uri.parse(ApiConstants.baseUrl);
    final scheme = baseUri.scheme == 'https' ? 'wss' : 'ws';
    return baseUri.replace(
      scheme: scheme,
      path: '/ws',
      query: null,
      fragment: null,
    );
  }

  Future<void> dispose() async {
    _disposed = true;
    _reconnectTimer?.cancel();
    await _socket?.close();
    _socket = null;
    await _controller.close();
  }
}

final webSocketServiceProvider = Provider<WebSocketService>((ref) {
  final service = WebSocketService();
  ref.onDispose(() {
    unawaited(service.dispose());
  });
  return service;
});