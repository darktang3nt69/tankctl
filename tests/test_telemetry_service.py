import unittest

from src.services.telemetry_service import TelemetryService


class TelemetryServiceNormalizationTests(unittest.TestCase):
    def test_normalize_temperature_zero_as_unavailable(self) -> None:
        self.assertIsNone(TelemetryService._normalize_metric("temperature", 0))

    def test_normalize_temperature_positive_value(self) -> None:
        self.assertEqual(
            TelemetryService._normalize_metric("temperature", 24.5),
            24.5,
        )

    def test_normalize_non_temperature_zero_remains_numeric(self) -> None:
        self.assertEqual(TelemetryService._normalize_metric("humidity", 0), 0.0)


if __name__ == '__main__':
    unittest.main()