import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/providers/app_settings_provider.dart';
import 'api_constants.dart';

final dioProvider = Provider<Dio>((ref) {
  final configuredBaseUrl =
      ref.watch(serverBaseUrlProvider).valueOrNull ?? ApiConstants.baseUrl;

  return Dio(
    BaseOptions(
      baseUrl: configuredBaseUrl,
      connectTimeout: const Duration(seconds: 5),
      receiveTimeout: const Duration(seconds: 10),
      headers: {'Content-Type': 'application/json'},
    ),
  );
});
