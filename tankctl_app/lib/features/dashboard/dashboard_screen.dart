import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/providers/dashboard_provider.dart';
import 'package:tankctl_app/providers/device_provider.dart';
import 'package:tankctl_app/providers/telemetry_provider.dart';
import 'package:tankctl_app/features/dashboard/widgets/dashboard_tab.dart';
import 'package:tankctl_app/features/dashboard/widgets/settings_tab.dart';
import 'package:tankctl_app/features/dashboard/widgets/quick_actions_fab.dart';

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
            const Text('TankCTL', style: TextStyle(fontWeight: FontWeight.bold)),
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
          DashboardTab(onRefresh: _refresh),
          const SettingsTab(),
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
      floatingActionButton: _selectedIndex == 0 ? const QuickActionsFab() : null,
    );
  }
}
