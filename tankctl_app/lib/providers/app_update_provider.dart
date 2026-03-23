import 'dart:async';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:open_file/open_file.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tankctl_app/services/app_update_service.dart';
import 'package:url_launcher/url_launcher.dart';

// ── SharedPreferences keys ───────────────────────────────────────────────────

const _keyLastChecked = 'app_update_last_checked';
const _keyLastSeenTag = 'app_update_last_seen_tag';
const _keyLastSeenAssetId = 'app_update_last_seen_asset_id';
const _keyLastSeenAssetUpdatedAt = 'app_update_last_seen_asset_updated_at';
const _keyDownloadedApkPath = 'app_update_downloaded_apk_path';

// ── State model ───────────────────────────────────────────────────────────────

enum UpdateStatus {
  idle,
  checking,
  upToDate,
  updateAvailable,
  downloading,
  readyToInstall,
  error,
}

class AppUpdateState {
  const AppUpdateState({
    this.status = UpdateStatus.idle,
    this.currentVersion = '',
    this.latestVersion,
    this.releaseName,
    this.releaseNotes,
    this.releaseHtmlUrl,
    this.assetDownloadUrl,
    this.assetId,
    this.assetUpdatedAt,
    this.downloadedApkPath,
    this.downloadProgress = 0.0,
    this.errorMessage,
    this.lastChecked,
  });

  final UpdateStatus status;
  final String currentVersion;
  final String? latestVersion;
  final String? releaseName;
  final String? releaseNotes;
  final String? releaseHtmlUrl;
  final String? assetDownloadUrl;
  final int? assetId;
  final String? assetUpdatedAt;
  final String? downloadedApkPath;
  final double downloadProgress;
  final String? errorMessage;
  final DateTime? lastChecked;

  AppUpdateState copyWith({
    UpdateStatus? status,
    String? currentVersion,
    String? latestVersion,
    String? releaseName,
    String? releaseNotes,
    String? releaseHtmlUrl,
    String? assetDownloadUrl,
    int? assetId,
    String? assetUpdatedAt,
    String? downloadedApkPath,
    double? downloadProgress,
    String? errorMessage,
    DateTime? lastChecked,
  }) {
    return AppUpdateState(
      status: status ?? this.status,
      currentVersion: currentVersion ?? this.currentVersion,
      latestVersion: latestVersion ?? this.latestVersion,
      releaseName: releaseName ?? this.releaseName,
      releaseNotes: releaseNotes ?? this.releaseNotes,
      releaseHtmlUrl: releaseHtmlUrl ?? this.releaseHtmlUrl,
      assetDownloadUrl: assetDownloadUrl ?? this.assetDownloadUrl,
      assetId: assetId ?? this.assetId,
      assetUpdatedAt: assetUpdatedAt ?? this.assetUpdatedAt,
      downloadedApkPath: downloadedApkPath ?? this.downloadedApkPath,
      downloadProgress: downloadProgress ?? this.downloadProgress,
      errorMessage: errorMessage ?? this.errorMessage,
      lastChecked: lastChecked ?? this.lastChecked,
    );
  }
}

// ── Notifier ──────────────────────────────────────────────────────────────────

class AppUpdateNotifier extends Notifier<AppUpdateState> {
  late final AppUpdateService _service;
  CancelToken? _downloadCancel;

  @override
  AppUpdateState build() {
    _service = AppUpdateService(ref.read(appUpdateDioProvider));
    unawaited(_restorePersistedState());
    return const AppUpdateState();
  }

  // ── Public API ──────────────────────────────────────────────────────────

  Future<void> checkForUpdate() async {
    if (state.status == UpdateStatus.checking ||
        state.status == UpdateStatus.downloading) {
      return;
    }

    state = state.copyWith(status: UpdateStatus.checking, errorMessage: null);

    try {
      final info = await PackageInfo.fromPlatform();
      final currentVersion = info.version;
      final release = await _service.fetchLatestRelease();

      final prefs = await SharedPreferences.getInstance();
      final lastSeenTag = prefs.getString(_keyLastSeenTag);
      final lastSeenAssetId = prefs.getInt(_keyLastSeenAssetId);
      final lastSeenAssetUpdatedAt = prefs.getString(_keyLastSeenAssetUpdatedAt);

      final now = DateTime.now();
      await prefs.setString(_keyLastChecked, now.toIso8601String());

      final isNewer = _service.isNewerThan(
        release: release,
        currentVersion: currentVersion,
        lastSeenTag: lastSeenTag,
        lastSeenAssetId: lastSeenAssetId,
        lastSeenAssetUpdatedAt: lastSeenAssetUpdatedAt,
      );

      if (!isNewer) {
        // Mark this fingerprint as seen so we don't re-prompt for same assets.
        await _saveFingerprint(release);
        state = state.copyWith(
          status: UpdateStatus.upToDate,
          currentVersion: currentVersion,
          latestVersion: release.tagName,
          lastChecked: now,
        );
        return;
      }

      state = state.copyWith(
        status: UpdateStatus.updateAvailable,
        currentVersion: currentVersion,
        latestVersion: release.tagName,
        releaseName: release.releaseName,
        releaseNotes: release.releaseNotes,
        releaseHtmlUrl: release.releaseHtmlUrl,
        assetDownloadUrl: release.assetDownloadUrl,
        assetId: release.assetId,
        assetUpdatedAt: release.assetUpdatedAt,
        lastChecked: now,
      );
    } catch (e) {
      state = state.copyWith(
        status: UpdateStatus.error,
        errorMessage: _friendlyError(e),
      );
    }
  }

  Future<void> downloadUpdate() async {
    final downloadUrl = state.assetDownloadUrl;
    final latestVersion = state.latestVersion;
    if (downloadUrl == null || latestVersion == null) return;
    if (state.status == UpdateStatus.downloading) return;

    _downloadCancel = CancelToken();
    state = state.copyWith(
      status: UpdateStatus.downloading,
      downloadProgress: 0.0,
      errorMessage: null,
    );

    try {
      final path = await _service.downloadApk(
        url: downloadUrl,
        tagName: latestVersion,
        cancelToken: _downloadCancel,
        onProgress: (p) {
          state = state.copyWith(
            status: UpdateStatus.downloading,
            downloadProgress: p,
          );
        },
      );

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_keyDownloadedApkPath, path);
      if (state.assetId != null) {
        await _saveFingerprint(
          _ReleaseFingerprint(
            tagName: latestVersion,
            assetId: state.assetId!,
            assetUpdatedAt: state.assetUpdatedAt ?? '',
          ),
        );
      }

      state = state.copyWith(
        status: UpdateStatus.readyToInstall,
        downloadedApkPath: path,
        downloadProgress: 1.0,
      );
    } on DioException catch (e) {
      if (e.type == DioExceptionType.cancel) {
        state = state.copyWith(status: UpdateStatus.updateAvailable);
      } else {
        state = state.copyWith(
          status: UpdateStatus.error,
          errorMessage: _friendlyError(e),
        );
      }
    } catch (e) {
      state = state.copyWith(
        status: UpdateStatus.error,
        errorMessage: _friendlyError(e),
      );
    }
  }

  Future<void> cancelDownload() async {
    _downloadCancel?.cancel('User cancelled');
  }

  Future<bool> installUpdate() async {
    final path = state.downloadedApkPath;
    if (path == null) return false;

    final file = File(path);
    if (!await file.exists()) {
      await _clearDownloadedApkFromPrefs();
      state = state.copyWith(
        status: UpdateStatus.updateAvailable,
        downloadedApkPath: null,
      );
      return false;
    }

    final result = await OpenFile.open(path);
    return result.type == ResultType.done;
  }

  Future<void> openReleasePage() async {
    final url = state.releaseHtmlUrl;
    if (url == null) return;
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  // ── Internal helpers ──────────────────────────────────────────────────

  Future<void> _restorePersistedState() async {
    final info = await PackageInfo.fromPlatform();
    final prefs = await SharedPreferences.getInstance();

    final checkedStr = prefs.getString(_keyLastChecked);
    final lastChecked =
        checkedStr != null ? DateTime.tryParse(checkedStr) : null;
    final downloadedPath = prefs.getString(_keyDownloadedApkPath);

    // Verify the downloaded file still exists.
    String? validPath;
    if (downloadedPath != null) {
      final file = File(downloadedPath);
      if (await file.exists()) {
        validPath = downloadedPath;
      } else {
        await _clearDownloadedApkFromPrefs();
      }
    }

    state = state.copyWith(
      currentVersion: info.version,
      downloadedApkPath: validPath,
      status: validPath != null ? UpdateStatus.readyToInstall : UpdateStatus.idle,
      lastChecked: lastChecked,
    );
  }

  Future<void> _saveFingerprint(dynamic releaseOrFingerprint) async {
    final prefs = await SharedPreferences.getInstance();
    if (releaseOrFingerprint is GithubReleaseInfo) {
      await prefs.setString(_keyLastSeenTag, releaseOrFingerprint.tagName);
      await prefs.setInt(_keyLastSeenAssetId, releaseOrFingerprint.assetId);
      await prefs.setString(
        _keyLastSeenAssetUpdatedAt,
        releaseOrFingerprint.assetUpdatedAt,
      );
    } else if (releaseOrFingerprint is _ReleaseFingerprint) {
      await prefs.setString(_keyLastSeenTag, releaseOrFingerprint.tagName);
      await prefs.setInt(_keyLastSeenAssetId, releaseOrFingerprint.assetId);
      await prefs.setString(
        _keyLastSeenAssetUpdatedAt,
        releaseOrFingerprint.assetUpdatedAt,
      );
    }
  }

  Future<void> _clearDownloadedApkFromPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyDownloadedApkPath);
  }

  String _friendlyError(Object e) {
    if (e is DioException) {
      if (e.type == DioExceptionType.connectionTimeout ||
          e.type == DioExceptionType.receiveTimeout ||
          e.type == DioExceptionType.sendTimeout) {
        return 'Connection timed out. Check your network.';
      }
      if (e.response?.statusCode == 404) {
        return 'No GitHub release found.';
      }
      if (e.response?.statusCode != null) {
        return 'GitHub API error (${e.response?.statusCode}).';
      }
      return 'Network error: ${e.message}';
    }
    return e.toString();
  }
}

// ── Private fingerprint helper (avoids casting GithubReleaseInfo twice) ──────

class _ReleaseFingerprint {
  const _ReleaseFingerprint({
    required this.tagName,
    required this.assetId,
    required this.assetUpdatedAt,
  });
  final String tagName;
  final int assetId;
  final String assetUpdatedAt;
}

// ── Providers ─────────────────────────────────────────────────────────────────

/// Dedicated Dio instance for GitHub API calls — no base URL, no auth headers
/// from the backend settings.
final appUpdateDioProvider = Provider<Dio>((ref) => Dio());

final appUpdateProvider =
    NotifierProvider<AppUpdateNotifier, AppUpdateState>(
      AppUpdateNotifier.new,
    );
