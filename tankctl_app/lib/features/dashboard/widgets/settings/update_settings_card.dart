import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tankctl_app/features/dashboard/widgets/settings/settings_card_shell.dart';
import 'package:tankctl_app/providers/app_update_provider.dart';

class UpdateSettingsCard extends ConsumerWidget {
  const UpdateSettingsCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final update = ref.watch(appUpdateProvider);
    final textTheme = Theme.of(context).textTheme;

    return SettingsCardShell(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.system_update_rounded),
              const SizedBox(width: 10),
              Text(
                'App Update',
                style: textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
              const Spacer(),
              if (update.status == UpdateStatus.updateAvailable ||
                  update.status == UpdateStatus.readyToInstall)
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.orangeAccent.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: Colors.orangeAccent.withValues(alpha: 0.6),
                    ),
                  ),
                  child: Text(
                    'Update Available',
                    style: textTheme.labelSmall?.copyWith(
                      color: Colors.orangeAccent,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 14),

          // ── Version rows ────────────────────────────────────────────────
          _InfoRow(
            label: 'Installed',
            value: update.currentVersion.isEmpty
                ? '—'
                : 'v${update.currentVersion}',
          ),
          if (update.latestVersion != null) ...[
            const SizedBox(height: 4),
            _InfoRow(
              label: 'Latest',
              value: update.latestVersion!.startsWith('v')
                  ? update.latestVersion!
                  : 'v${update.latestVersion}',
              highlight: update.status == UpdateStatus.updateAvailable ||
                  update.status == UpdateStatus.readyToInstall,
            ),
          ],
          if (update.lastChecked != null) ...[
            const SizedBox(height: 4),
            _InfoRow(
              label: 'Checked',
              value: _formatChecked(update.lastChecked!),
            ),
          ],

          // ── Release notes ───────────────────────────────────────────────
          if ((update.releaseNotes ?? '').isNotEmpty &&
              update.status != UpdateStatus.upToDate) ...[
            const SizedBox(height: 12),
            Text(
              update.releaseName ?? update.latestVersion ?? '',
              style: textTheme.labelMedium?.copyWith(
                fontWeight: FontWeight.w700,
                color: Colors.white70,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              update.releaseNotes!,
              style: textTheme.bodySmall?.copyWith(color: Colors.white54),
              maxLines: 5,
              overflow: TextOverflow.ellipsis,
            ),
          ],

          // ── Download progress ───────────────────────────────────────────
          if (update.status == UpdateStatus.downloading) ...[
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: LinearProgressIndicator(
                    value: update.downloadProgress,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
                const SizedBox(width: 10),
                Text(
                  '${(update.downloadProgress * 100).toStringAsFixed(0)}%',
                  style: textTheme.bodySmall,
                ),
              ],
            ),
          ],

          // ── Error ───────────────────────────────────────────────────────
          if (update.status == UpdateStatus.error &&
              update.errorMessage != null) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                const Icon(
                  Icons.error_outline_rounded,
                  size: 16,
                  color: Colors.redAccent,
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    update.errorMessage!,
                    style: textTheme.bodySmall?.copyWith(
                      color: Colors.redAccent,
                    ),
                  ),
                ),
              ],
            ),
          ],

          const SizedBox(height: 16),

          // ── Action buttons ──────────────────────────────────────────────
          _ActionButtons(update: update),
        ],
      ),
    );
  }

  String _formatChecked(DateTime dt) {
    final now = DateTime.now();
    final diff = now.difference(dt);
    if (diff.inSeconds < 60) return 'Just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({
    required this.label,
    required this.value,
    this.highlight = false,
  });

  final String label;
  final String value;
  final bool highlight;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Row(
      children: [
        Text(
          '$label:',
          style: textTheme.bodySmall?.copyWith(color: Colors.white54),
        ),
        const SizedBox(width: 6),
        Text(
          value,
          style: textTheme.bodySmall?.copyWith(
            color: highlight ? Colors.orangeAccent : Colors.white70,
            fontWeight: highlight ? FontWeight.w600 : FontWeight.normal,
          ),
        ),
      ],
    );
  }
}

class _ActionButtons extends ConsumerWidget {
  const _ActionButtons({required this.update});

  final AppUpdateState update;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifier = ref.read(appUpdateProvider.notifier);

    return switch (update.status) {
      UpdateStatus.idle || UpdateStatus.upToDate || UpdateStatus.error => Wrap(
        spacing: 10,
        runSpacing: 8,
        children: [
          FilledButton.icon(
            onPressed: () => notifier.checkForUpdate(),
            icon: const Icon(Icons.refresh_rounded),
            label: const Text('Check now'),
          ),
          if (update.status == UpdateStatus.error)
            Text(
              update.latestVersion != null ? 'Last known: ${update.latestVersion}' : '',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.white38,
              ),
            ),
        ],
      ),
      UpdateStatus.checking => Row(
        children: [
          const SizedBox(
            width: 18,
            height: 18,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
          const SizedBox(width: 10),
          Text(
            'Checking for updates…',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
      UpdateStatus.updateAvailable => Wrap(
        spacing: 10,
        runSpacing: 8,
        children: [
          FilledButton.icon(
            onPressed: () => notifier.downloadUpdate(),
            icon: const Icon(Icons.download_rounded),
            label: const Text('Download update'),
          ),
          OutlinedButton.icon(
            onPressed: () => notifier.openReleasePage(),
            icon: const Icon(Icons.open_in_new_rounded, size: 16),
            label: const Text('Release notes'),
          ),
          OutlinedButton(
            onPressed: () => notifier.checkForUpdate(),
            child: const Text('Re-check'),
          ),
        ],
      ),
      UpdateStatus.downloading => OutlinedButton.icon(
        onPressed: () => notifier.cancelDownload(),
        icon: const Icon(Icons.close_rounded, size: 16),
        label: const Text('Cancel'),
      ),
      UpdateStatus.readyToInstall => Wrap(
        spacing: 10,
        runSpacing: 8,
        children: [
          FilledButton.icon(
            onPressed: () async {
              final ok = await notifier.installUpdate();
              if (!ok && context.mounted) {
                await notifier.openReleasePage();
              }
            },
            icon: const Icon(Icons.install_mobile_rounded),
            label: const Text('Install update'),
          ),
          OutlinedButton.icon(
            onPressed: () => notifier.openReleasePage(),
            icon: const Icon(Icons.open_in_new_rounded, size: 16),
            label: const Text('Open release page'),
          ),
        ],
      ),
    };
  }
}
