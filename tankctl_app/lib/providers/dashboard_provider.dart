import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/providers/device_provider.dart';
import 'package:tankctl_app/services/telemetry_service.dart';

class DashboardOverview {
  const DashboardOverview({
    required this.totalCount,
    required this.onlineCount,
    this.avgTemp,
  });

  final int totalCount;
  final int onlineCount;
  final double? avgTemp;
}

final dashboardOverviewProvider = FutureProvider<DashboardOverview>((ref) async {
  final devices = await ref.watch(devicesListProvider.future);
  final onlineCount = devices.where((d) => d['status'] == 'online').length;

  final service = ref.watch(telemetryServiceProvider);
  final temps = await Future.wait(
    devices.map((d) async {
      try {
        return await service.getLatestTemperature(d['device_id'] as String);
      } catch (_) {
        return null;
      }
    }),
  );

  final validTemps = temps.whereType<double>().toList();
  final avgTemp = validTemps.isEmpty
      ? null
      : validTemps.reduce((a, b) => a + b) / validTemps.length;

  return DashboardOverview(
    totalCount: devices.length,
    onlineCount: onlineCount,
    avgTemp: avgTemp,
  );
});
