class ApiConstants {
  static const baseUrl = String.fromEnvironment(
    'TANKCTL_BASE_URL',
    defaultValue: 'http://192.168.1.100:8000',
  );
  static const defaultDeviceId = 'tank1';

  static String get backendLabel {
    final uri = Uri.tryParse(baseUrl);
    if (uri == null || uri.host.isEmpty) {
      return baseUrl;
    }
    final port = uri.hasPort ? ':${uri.port}' : '';
    return '${uri.host}$port';
  }
}
