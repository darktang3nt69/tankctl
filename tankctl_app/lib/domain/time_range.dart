/// Represents a selectable time range for telemetry data visualization
class TimeRange {
  final String label;
  final Duration duration;
  final int apiLimit;

  const TimeRange({
    required this.label,
    required this.duration,
    required this.apiLimit,
  });

  /// Standard time ranges for telemetry visualization
  static const List<TimeRange> common = [
    TimeRange(label: '1h', duration: Duration(hours: 1), apiLimit: 60),
    TimeRange(label: '24h', duration: Duration(hours: 24), apiLimit: 1440),
    TimeRange(label: '7d', duration: Duration(days: 7), apiLimit: 336),
    TimeRange(label: '30d', duration: Duration(days: 30), apiLimit: 1440),
  ];

  static const TimeRange defaultRange = TimeRange(
    label: '24h',
    duration: Duration(hours: 24),
    apiLimit: 336,
  );

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is TimeRange &&
          runtimeType == other.runtimeType &&
          label == other.label &&
          duration == other.duration;

  @override
  int get hashCode => label.hashCode ^ duration.hashCode;
}
