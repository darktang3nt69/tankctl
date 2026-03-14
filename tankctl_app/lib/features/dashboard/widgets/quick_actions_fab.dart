import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/providers/device_provider.dart';
import 'package:tankctl_app/providers/light_provider.dart';
import 'package:tankctl_app/services/device_service.dart';

class QuickActionsFab extends ConsumerStatefulWidget {
  const QuickActionsFab({super.key});

  @override
  ConsumerState<QuickActionsFab> createState() => _QuickActionsFabState();
}

class _QuickActionsFabState extends ConsumerState<QuickActionsFab> with SingleTickerProviderStateMixin {
    Offset _fabOffset = Offset.zero;
  bool _expanded = false;
  bool _busy = false;

  void _toggle() {
    HapticFeedback.mediumImpact();
    setState(() => _expanded = !_expanded);
  }

  Future<void> _confirmAndRun(String title, String message, Future<void> Function(List<String>) action) async {
    final devices = ref.read(devicesListProvider).valueOrNull;
    if (devices == null || devices.isEmpty) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.of(context).pop(true), child: const Text('Confirm')),
        ],
      ),
    );
    if (confirmed == true) {
      setState(() => _busy = true);
      await action([for (final d in devices) d['device_id'] as String]);
      setState(() => _busy = false);
      if (mounted) {
        String snackText;
        if (title.contains('Reboot')) {
          snackText = 'All devices rebooted';
        } else if (title.contains('Turn All Lights ON')) {
          snackText = 'All lights turned on';
        } else if (title.contains('Turn All Lights OFF')) {
          snackText = 'All lights turned off';
        } else if (title.contains('Acknowledge')) {
          snackText = 'All warnings acknowledged';
        } else {
          snackText = 'Action complete';
        }
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(snackText)),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // Removed unused theme variable
    final devicesAsync = ref.watch(devicesListProvider);
    Color fabColor = Colors.blueAccent;
    IconData fabIcon = Icons.flash_on_rounded;
    bool hasWarning = false;
    bool hasOffline = false;
    bool allHealthy = false;

    devicesAsync.whenData((devices) {
      if (devices.isNotEmpty) {
        hasOffline = devices.any((d) => d['status'] == 'offline');
        hasWarning = devices.any((d) => d['status'] == 'highTemp' || d['status'] == 'lowTemp' || d['status'] == 'unknown');
        allHealthy = devices.every((d) => d['status'] == 'healthy' || d['status'] == 'ok');
      }
    });

    if (hasOffline) {
      fabColor = Colors.redAccent;
      fabIcon = Icons.warning_amber_rounded;
    } else if (hasWarning) {
      fabColor = Colors.orangeAccent;
      fabIcon = Icons.error_outline_rounded;
    } else if (allHealthy) {
      fabColor = Colors.green;
      fabIcon = Icons.check_circle_rounded;
    }

    return Stack(
      alignment: Alignment.bottomRight,
      children: [
        AnimatedSlide(
          offset: _expanded ? Offset.zero : const Offset(0, 0.2),
          duration: const Duration(milliseconds: 350),
          curve: Curves.easeOutCubic,
          child: AnimatedOpacity(
            opacity: _expanded ? 1.0 : 0.0,
            duration: const Duration(milliseconds: 350),
            curve: Curves.easeOutCubic,
            child: Padding(
              padding: const EdgeInsets.only(bottom: 80, right: 8),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  FloatingActionButton(
                    heroTag: 'fab-reboot',
                    mini: true,
                    backgroundColor: Colors.blueAccent,
                    onPressed: _busy
                        ? null
                        : () {
                            HapticFeedback.mediumImpact();
                            _confirmAndRun(
                              'Reboot All Devices',
                              'Are you sure you want to reboot all tanks?',
                              (ids) async {
                                final svc = ref.read(deviceServiceProvider);
                                for (final id in ids) {
                                  await svc.rebootDevice(id);
                                }
                              },
                            );
                          },
                    tooltip: 'Reboot All',
                    child: const Icon(Icons.autorenew_rounded),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      FloatingActionButton(
                        heroTag: 'fab-light-on',
                        mini: true,
                        backgroundColor: Colors.yellow.shade700,
                        onPressed: _busy
                            ? null
                            : () {
                                HapticFeedback.mediumImpact();
                                _confirmAndRun(
                                  'Turn All Lights ON',
                                  'Turn ON lights for all tanks?',
                                  (ids) async {
                                    for (final id in ids) {
                                      final notifier = ref.read(lightStateFamilyProvider(id).notifier);
                                      await notifier.toggle(true);
                                    }
                                  },
                                );
                              },
                        tooltip: 'Lights ON',
                        child: const Icon(Icons.wb_incandescent_rounded, color: Colors.amberAccent),
                      ),
                      const SizedBox(width: 8),
                      FloatingActionButton(
                        heroTag: 'fab-light-off',
                        mini: true,
                        backgroundColor: Colors.grey.shade700,
                        onPressed: _busy
                            ? null
                            : () {
                                HapticFeedback.mediumImpact();
                                _confirmAndRun(
                                  'Turn All Lights OFF',
                                  'Turn OFF lights for all tanks?',
                                  (ids) async {
                                    for (final id in ids) {
                                      final notifier = ref.read(lightStateFamilyProvider(id).notifier);
                                      await notifier.toggle(false);
                                    }
                                  },
                                );
                              },
                        tooltip: 'Lights OFF',
                        child: const Icon(Icons.nightlight_round, color: Colors.blueGrey),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  FloatingActionButton(
                    heroTag: 'fab-ack',
                    mini: true,
                    backgroundColor: Colors.green,
                    onPressed: _busy
                        ? null
                        : () {
                            HapticFeedback.mediumImpact();
                            _confirmAndRun(
                              'Acknowledge All Warnings',
                              'Acknowledge all warnings for all tanks?',
                              (ids) async {
                                final svc = ref.read(deviceServiceProvider);
                                for (final id in ids) {
                                  await svc.acknowledgeWarning(id, 'sensor_unavailable');
                                }
                              },
                            );
                          },
                    tooltip: 'Acknowledge All Warnings',
                    child: const Icon(Icons.verified_rounded, color: Colors.lightGreenAccent),
                  ),
                ],
              ),
            ),
          ),
        ),
        Positioned(
          right: _fabOffset.dx,
          bottom: _fabOffset.dy,
          child: GestureDetector(
            onPanUpdate: (details) {
              setState(() {
                _fabOffset += details.delta;
              });
            },
            child: Tooltip(
              message: 'Quick Actions',
              child: AnimatedScale(
                scale: _expanded ? 0.8 : 1.0,
                duration: const Duration(milliseconds: 400),
                curve: Curves.easeOutBack,
                child: AnimatedOpacity(
                  opacity: _expanded ? 0.7 : 1.0,
                  duration: const Duration(milliseconds: 400),
                  curve: Curves.easeOut,
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      boxShadow: [
                        BoxShadow(
                          color: fabColor.withOpacity(0.6),
                          blurRadius: 18,
                          spreadRadius: 2,
                          offset: const Offset(0, 4),
                        ),
                      ],
                      shape: BoxShape.circle,
                    ),
                    child: FloatingActionButton(
                      heroTag: 'fab-main',
                      backgroundColor: fabColor,
                      onPressed: _busy ? null : _toggle,
                      child: _busy
                          ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : Icon(_expanded ? Icons.close : fabIcon),
                      tooltip: 'Quick Actions',
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
