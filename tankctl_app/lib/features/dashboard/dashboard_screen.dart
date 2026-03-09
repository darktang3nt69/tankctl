import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/features/tank_detail/tank_detail_screen.dart';
import 'package:tankctl_app/providers/app_settings_provider.dart';
import 'package:tankctl_app/providers/dashboard_provider.dart';
import 'package:tankctl_app/providers/device_provider.dart';
import 'package:tankctl_app/providers/telemetry_provider.dart';
import 'package:tankctl_app/widgets/tank_card.dart';
import 'package:tankctl_app/widgets/tank_overview_card.dart';

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  int _selectedIndex = 0;

  void _refresh() {
    ref.invalidate(devicesListProvider);
    ref.invalidate(dashboardOverviewProvider);
    ref.invalidate(temperatureHistoryProvider);
    ref.invalidate(deviceShadowProvider);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 20,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('TankCtl', style: TextStyle(fontWeight: FontWeight.bold)),
            Text(
              'My Tanks',
              style: Theme.of(context)
                  .textTheme
                  .labelSmall
                  ?.copyWith(color: Colors.white54),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh',
            onPressed: _refresh,
          ),
        ],
      ),
      body: IndexedStack(
        index: _selectedIndex,
        children: [
          _DashboardTab(onRefresh: _refresh),
          const _SettingsTab(),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (i) => setState(() => _selectedIndex = i),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard),
            label: 'Dashboard',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings),
            label: 'Settings',
          ),
        ],
      ),
    );
  }
}

class _DashboardTab extends ConsumerStatefulWidget {
  const _DashboardTab({required this.onRefresh});

  final VoidCallback onRefresh;

  @override
  ConsumerState<_DashboardTab> createState() => _DashboardTabState();
}

class _DashboardTabState extends ConsumerState<_DashboardTab> {
  bool _showOnlineOnly = false;

  @override
  Widget build(BuildContext context) {
    final devicesAsync = ref.watch(devicesListProvider);
    final textTheme = Theme.of(context).textTheme;

    return RefreshIndicator(
      onRefresh: () async => widget.onRefresh(),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          // ── Overview summary card ──────────────────────────────────────
          const TankOverviewCard(),
          const SizedBox(height: 24),

          // ── Section label + online filter ──────────────────────────────
          Row(
            children: [
              Text(
                'MY TANKS',
                style: textTheme.labelSmall?.copyWith(
                  color: Colors.white38,
                  letterSpacing: 1.4,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const Spacer(),
              FilterChip(
                label: const Text('Online only'),
                selected: _showOnlineOnly,
                onSelected: (v) => setState(() => _showOnlineOnly = v),
                visualDensity: VisualDensity.compact,
              ),
            ],
          ),
          const SizedBox(height: 12),

          // ── Tank cards ─────────────────────────────────────────────────
          devicesAsync.when(
            data: (devices) {
              var sorted = [...devices]
                ..sort((a, b) => (a['device_id'] as String)
                    .compareTo(b['device_id'] as String));
              if (_showOnlineOnly) {
                sorted =
                    sorted.where((d) => d['status'] == 'online').toList();
              }
              return Column(
                children: [
                  for (final device in sorted) ...[
                    TankCard(
                      deviceId: device['device_id'] as String,
                      isOnline: device['status'] == 'online',
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => TankDetailScreen(
                            deviceId: device['device_id'] as String,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                  ],
                ],
              );
            },
            loading: () => const Padding(
              padding: EdgeInsets.symmetric(vertical: 48),
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (e, _) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 48),
              child: Column(
                children: [
                  const Icon(Icons.wifi_off_rounded, size: 56, color: Colors.white12),
                  const SizedBox(height: 16),
                  Text(
                    'Could not reach backend',
                    style: textTheme.bodyMedium?.copyWith(color: Colors.white38),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    '192.168.1.100:8000',
                    style: textTheme.labelSmall?.copyWith(color: Colors.white24),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SettingsTab extends ConsumerWidget {
  const _SettingsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final refreshIntervalAsync = ref.watch(liveRefreshIntervalProvider);
    final textTheme = Theme.of(context).textTheme;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(
          'Live Updates',
          style: textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'WebSocket events apply immediately. This interval forces a background resync so the dashboard stays current within a few seconds even if an event is missed.',
          style: textTheme.bodyMedium?.copyWith(color: Colors.white60),
        ),
        const SizedBox(height: 20),
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: const Color(0xFF1E293B),
            borderRadius: BorderRadius.circular(16),
          ),
          child: refreshIntervalAsync.when(
            data: (seconds) => Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.bolt_rounded),
                    const SizedBox(width: 10),
                    Text(
                      'Live refresh interval',
                      style: textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const Spacer(),
                    Text(
                      '$seconds s',
                      style: textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Slider(
                  value: seconds.toDouble(),
                  min: 1,
                  max: 10,
                  divisions: 9,
                  label: '$seconds s',
                  onChanged: (value) {
                    ref
                        .read(liveRefreshIntervalProvider.notifier)
                        .setLiveRefreshInterval(value.round());
                  },
                ),
                const SizedBox(height: 8),
                Text(
                  'Recommended: 3-5 seconds. Lower values feel more instant but send more HTTP refresh traffic.',
                  style: textTheme.bodySmall?.copyWith(color: Colors.white54),
                ),
              ],
            ),
            loading: () => const SizedBox(
              height: 80,
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (error, _) => Text(
              'Could not load settings: $error',
              style: textTheme.bodyMedium?.copyWith(color: Colors.redAccent),
            ),
          ),
        ),
      ],
    );
  }
}
