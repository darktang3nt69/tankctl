import 'package:flutter/material.dart';
import 'package:tankctl_app/domain/device_detail.dart';
import 'package:tankctl_app/utils/app_icons.dart';

/// Tank header with health metrics - combined into one compact pane
class TankHeaderWithHealthSection extends StatelessWidget {
  final DeviceDetail device;

  const TankHeaderWithHealthSection({super.key, required this.device});

  @override
  Widget build(BuildContext context) {
    final isOnline = device.status == 'online';
    final statusColor = isOnline ? Colors.green : Colors.red;
    final textTheme = Theme.of(context).textTheme;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Container(
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
        decoration: BoxDecoration(
          color: Colors.grey.withValues(alpha: 0.05),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.grey.withValues(alpha: 0.15)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Single row: name + status badge
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        device.deviceName ?? device.deviceId,
                        style: textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      if (device.lastSeen != null)
                        Text(
                          _formatTime(device.lastSeen!),
                          style: textTheme.labelSmall?.copyWith(
                            color: Colors.grey,
                          ),
                        ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: statusColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: statusColor.withValues(alpha: 0.3)),
                  ),
                  child: Text(
                    device.status.toUpperCase(),
                    style: TextStyle(
                      color: statusColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 11,
                      letterSpacing: 0.8,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            // Compact metrics row: WiFi · Uptime · Location
            Row(
              children: [
                _buildInlineMetric(
                  context,
                  icon: _rssiIcon(device.rssi),
                  iconColor: _rssiColor(device.rssi, isOnline),
                  label: device.rssi != null ? '${device.rssi} dBm' : '—',
                ),
                _buildDivider(),
                _buildInlineMetric(
                  context,
                  icon: AppIcons.time,
                  iconColor: Colors.white54,
                  label: _formatUptime(device.uptimeMs ?? 0),
                ),
                if (device.location != null) ...[
                  _buildDivider(),
                  _buildInlineMetric(
                    context,
                    icon: Icons.location_on_outlined,
                    iconColor: Colors.white38,
                    label: device.location!,
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInlineMetric(
    BuildContext context, {
    required IconData icon,
    required Color iconColor,
    required String label,
  }) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: iconColor),
        const SizedBox(width: 4),
        Text(
          label,
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
            color: Colors.white70,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  Widget _buildDivider() => const Padding(
    padding: EdgeInsets.symmetric(horizontal: 10),
    child: Text('·', style: TextStyle(color: Colors.white24, fontSize: 16)),
  );

  IconData _rssiIcon(int? rssi) {
    if (rssi == null) return AppIcons.wifiOff;
    if (rssi > -60) return AppIcons.wifiStrong;
    if (rssi >= -75) return AppIcons.wifiMedium;
    return AppIcons.wifiWeak;
  }

  Color _rssiColor(int? rssi, bool isOnline) {
    if (!isOnline || rssi == null) return Colors.white38;
    if (rssi > -60) return Colors.green;
    if (rssi >= -75) return Colors.orange;
    return Colors.red;
  }

  String _formatUptime(int uptimeMs) {
    final duration = Duration(milliseconds: uptimeMs);
    final days = duration.inDays;
    final hours = duration.inHours % 24;
    final minutes = duration.inMinutes % 60;
    
    if (days > 0) {
      return '${days}d ${hours}h';
    } else if (hours > 0) {
      return '${hours}h ${minutes}m';
    } else {
      return '${minutes}m';
    }
  }

  String _formatTime(String timestamp) {
    try {
      final dt = DateTime.parse(timestamp);
      final now = DateTime.now();
      final diff = now.difference(dt);

      if (diff.inMinutes < 1) {
        return 'Just now';
      } else if (diff.inMinutes < 60) {
        return '${diff.inMinutes}m ago';
      } else if (diff.inHours < 24) {
        return '${diff.inHours}h ago';
      } else {
        return '${diff.inDays}d ago';
      }
    } catch (_) {
      return timestamp;
    }
  }
}
