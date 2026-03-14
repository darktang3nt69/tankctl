import 'package:flutter/material.dart';
import 'package:tankctl_app/utils/app_icons.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';
import 'package:tankctl_app/providers/dashboard_provider.dart';

/// Gradient summary card at the top of the dashboard showing online count
/// and average temperature across all devices.
class TankOverviewCard extends ConsumerWidget {
  const TankOverviewCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final overviewAsync = ref.watch(dashboardOverviewProvider);
    final textTheme = Theme.of(context).textTheme;

    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            TankCtlColors.primary.withValues(alpha: 0.18),
            TankCtlColors.card,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: TankCtlColors.primary.withValues(alpha: 0.25)),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
      child: overviewAsync.when(
        data: (overview) => Row(
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'System Overview',
                  style: textTheme.labelSmall?.copyWith(color: Colors.white54),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Container(
                      width: 10,
                      height: 10,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: TankCtlColors.success,
                        boxShadow: [
                          BoxShadow(
                            color: TankCtlColors.success.withValues(alpha: 0.5),
                            blurRadius: 4,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      '${overview.onlineCount} of ${overview.totalCount} Online',
                      style: textTheme.titleMedium?.copyWith(color: Colors.white),
                    ),
                  ],
                ),
              ],
            ),
            const Spacer(),
            if (overview.avgTempOnlineOnly != null)
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    'Avg Temp',
                    style: textTheme.labelSmall?.copyWith(color: Colors.white54),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${overview.avgTempOnlineOnly!.toStringAsFixed(1)}°C',
                    style: textTheme.headlineSmall?.copyWith(
                      color: TankCtlColors.primary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
          ],
        ),
        loading: () => const SizedBox(
          height: 48,
          child: Center(child: CircularProgressIndicator()),
        ),
        error: (e, _) => Row(
          children: [
            const Icon(AppIcons.cloudOffOutlined, color: Colors.white38, size: 20),
            const SizedBox(width: 10),
            Text(
              'Could not load overview',
              style: textTheme.labelMedium?.copyWith(color: Colors.white38),
            ),
          ],
        ),
      ),
    );
  }
}
