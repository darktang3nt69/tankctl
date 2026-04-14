import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/providers/device_provider.dart';
import 'package:tankctl_app/services/telemetry_service.dart';

class DashboardOverview {
  const DashboardOverview({
    required this.totalCount,
    required this.onlineCount,
    required this.offlineCount,
    this.avgTempOnlineOnly,
    this.hottestDeviceId,
    this.hottestTemp,
    this.coldestDeviceId,
    this.coldestTemp,
  });

  final int totalCount;
  final int onlineCount;
  final int offlineCount;
  final double? avgTempOnlineOnly;
  final String? hottestDeviceId;
  final double? hottestTemp;
  final String? coldestDeviceId;
  final double? coldestTemp;
}

final dashboardOverviewProvider = FutureProvider<DashboardOverview>((ref) async {
  final devices = await ref.watch(devicesListProvider.future);
  final onlineDevices =
      devices.where((d) => d['status'] == 'online').toList(growable: false);
  final onlineCount = onlineDevices.length;
  final offlineCount = devices.length - onlineCount;

  final service = ref.watch(telemetryServiceProvider);
  final temps = await Future.wait(
    onlineDevices.map((d) async {
      try {
        final deviceId = d['device_id'] as String;
        final temp = await service.getLatestTemperature(deviceId);
        return (deviceId: deviceId, temp: temp);
      } catch (_) {
        return (deviceId: d['device_id'] as String, temp: null);
      }
    }),
  );

  final validTemps = temps.where((entry) => entry.temp != null).toList(growable: false);
  final avgTemp = validTemps.isEmpty
      ? null
      : validTemps.map((e) => e.temp!).reduce((a, b) => a + b) /
          validTemps.length;

  String? hottestDeviceId;
  double? hottestTemp;
  String? coldestDeviceId;
  double? coldestTemp;
  for (final entry in validTemps) {
    final t = entry.temp!;
    if (hottestTemp == null || t > hottestTemp) {
      hottestTemp = t;
      hottestDeviceId = entry.deviceId;
    }
    if (coldestTemp == null || t < coldestTemp) {
      coldestTemp = t;
      coldestDeviceId = entry.deviceId;
    }
  }

  return DashboardOverview(
    totalCount: devices.length,
    onlineCount: onlineCount,
    offlineCount: offlineCount,
    avgTempOnlineOnly: avgTemp,
    hottestDeviceId: hottestDeviceId,
    hottestTemp: hottestTemp,
    coldestDeviceId: coldestDeviceId,
    coldestTemp: coldestTemp,
  );
});
