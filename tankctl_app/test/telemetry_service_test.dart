import 'package:flutter_test/flutter_test.dart';
import 'package:tankctl_app/services/telemetry_service.dart';

void main() {
  group('normalizeTemperatureReading', () {
    test('treats zero as unavailable', () {
      expect(normalizeTemperatureReading(0), isNull);
      expect(normalizeTemperatureReading(0.0), isNull);
    });

    test('returns null for missing values', () {
      expect(normalizeTemperatureReading(null), isNull);
    });

    test('keeps positive readings', () {
      expect(normalizeTemperatureReading(24.8), 24.8);
    });
  });
}
