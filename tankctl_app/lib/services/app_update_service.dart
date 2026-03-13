import 'dart:io';

import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';

const _githubApiBase = 'https://api.github.com';
const _repo = 'darktang3nt69/tankctl';
const _preferredAssetName = 'app-release.apk';

/// Parsed metadata from the latest GitHub release, plus resolved asset info.
class GithubReleaseInfo {
  const GithubReleaseInfo({
    required this.tagName,
    required this.releaseName,
    required this.releaseNotes,
    required this.releaseHtmlUrl,
    required this.assetDownloadUrl,
    required this.assetId,
    required this.assetUpdatedAt,
    required this.publishedAt,
  });

  final String tagName;
  final String releaseName;
  final String releaseNotes;
  final String releaseHtmlUrl;
  final String assetDownloadUrl;
  final int assetId;
  final String assetUpdatedAt;
  final DateTime publishedAt;
}

/// Compares two version strings (with optional leading 'v').
/// Returns positive if [a] > [b], negative if [a] < [b], 0 if equal.
int compareVersions(String a, String b) {
  final pa = _parseVersion(a);
  final pb = _parseVersion(b);
  for (var i = 0; i < 3; i++) {
    final diff = pa[i] - pb[i];
    if (diff != 0) return diff;
  }
  return 0;
}

List<int> _parseVersion(String v) {
  final normalized = v.startsWith('v') ? v.substring(1) : v;
  final parts = normalized.split('.').map((p) {
    final digits = p.replaceAll(RegExp(r'[^0-9]'), '');
    return digits.isEmpty ? 0 : int.parse(digits);
  }).toList();
  while (parts.length < 3) {
    parts.add(0);
  }
  return parts;
}

class AppUpdateService {
  AppUpdateService(this._dio);

  final Dio _dio;

  /// Fetches the latest non-draft, non-prerelease GitHub release.
  Future<GithubReleaseInfo> fetchLatestRelease() async {
    final response = await _dio.get<Map<String, dynamic>>(
      '$_githubApiBase/repos/$_repo/releases/latest',
      options: Options(
        headers: {'Accept': 'application/vnd.github+json'},
        sendTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 15),
      ),
    );
    final data = response.data;
    if (data == null) throw Exception('Empty response from GitHub API');

    final assets = (data['assets'] as List<dynamic>? ?? []);
    final apkAsset =
        assets.firstWhere(
              (a) => (a as Map)['name'] == _preferredAssetName,
              orElse: () => assets.firstWhere(
                (a) => ((a as Map)['name'] as String).endsWith('.apk'),
                orElse: () =>
                    throw Exception('No APK asset found in latest release'),
              ),
            )
            as Map<String, dynamic>;

    return GithubReleaseInfo(
      tagName: data['tag_name'] as String,
      releaseName: (data['name'] as String?) ?? data['tag_name'] as String,
      releaseNotes: _trimNotes(data['body'] as String? ?? ''),
      releaseHtmlUrl: data['html_url'] as String,
      assetDownloadUrl: apkAsset['browser_download_url'] as String,
      assetId: apkAsset['id'] as int,
      assetUpdatedAt: apkAsset['updated_at'] as String,
      publishedAt: DateTime.parse(data['published_at'] as String),
    );
  }

  /// Returns true if [release] represents a new version or a changed asset
  /// compared to the stored fingerprint.
  bool isNewerThan({
    required GithubReleaseInfo release,
    required String currentVersion,
    required String? lastSeenTag,
    required int? lastSeenAssetId,
    required String? lastSeenAssetUpdatedAt,
  }) {
    // Newer tag always wins.
    if (compareVersions(release.tagName, currentVersion) > 0) return true;

    // Same tag but asset replaced (clobbered) on the same release.
    if (lastSeenTag != null &&
        release.tagName == lastSeenTag &&
        (lastSeenAssetId != release.assetId ||
            lastSeenAssetUpdatedAt != release.assetUpdatedAt)) {
      return true;
    }

    // First time ever seeing this release (no stored fingerprint yet).
    if (lastSeenTag == null &&
        compareVersions(release.tagName, currentVersion) == 0) {
      // Same version already installed and never seen from GitHub — no update.
      return false;
    }

    return false;
  }

  /// Downloads the APK to the app's external files directory and streams
  /// progress via [onProgress] (0.0 – 1.0). Returns the local file path.
  Future<String> downloadApk({
    required String url,
    required String tagName,
    void Function(double progress)? onProgress,
    CancelToken? cancelToken,
  }) async {
    final dir = Platform.isAndroid
        ? (await getExternalStorageDirectory() ??
              await getApplicationDocumentsDirectory())
        : await getApplicationDocumentsDirectory();
    final filePath =
        '${dir.path}/update_${tagName.replaceAll(RegExp(r'[^a-zA-Z0-9._-]'), '_')}.apk';
    final file = File(filePath);
    if (await file.exists()) await file.delete();

    await _dio.download(
      url,
      filePath,
      cancelToken: cancelToken,
      onReceiveProgress: (received, total) {
        if (total > 0 && onProgress != null) {
          onProgress(received / total);
        }
      },
    );
    return filePath;
  }

  String _trimNotes(String body) {
    const maxLen = 400;
    final trimmed = body.trim();
    if (trimmed.length <= maxLen) return trimmed;
    final cutoff = trimmed.lastIndexOf(' ', maxLen);
    return '${trimmed.substring(0, cutoff > 0 ? cutoff : maxLen)}…';
  }
}
