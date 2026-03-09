import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/services/websocket_service.dart';

final webSocketEventsProvider = StreamProvider<Map<String, dynamic>>((ref) {
  final service = ref.watch(webSocketServiceProvider);
  unawaited(service.connect());
  return service.stream;
});