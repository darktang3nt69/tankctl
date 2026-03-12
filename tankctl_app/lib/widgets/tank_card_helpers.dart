DateTime? parseIsoToLocal(String? raw) {
  if (raw == null) {
    return null;
  }
  return DateTime.tryParse(raw)?.toLocal();
}

String emojiForDevice(String deviceId) {
  const emojis = ['🐠', '🌿', '🪸', '🐡', '🦀', '🐙', '🦑', '🐬'];
  return emojis[deviceId.hashCode.abs() % emojis.length];
}

String displayNameFromDeviceId(String id) => id
    .replaceAll(RegExp(r'[_\-]'), ' ')
    .split(' ')
    .map((w) => w.isEmpty ? '' : '${w[0].toUpperCase()}${w.substring(1)}')
    .join(' ');

String formatAgeFromLastSeen(DateTime? lastSeen) {
  if (lastSeen == null) {
    return 'No data';
  }
  final diff = DateTime.now().difference(lastSeen);
  if (diff.inSeconds < 60) {
    return '${diff.inSeconds}s ago';
  }
  if (diff.inMinutes < 60) {
    return '${diff.inMinutes}m ago';
  }

  final h = lastSeen.hour.toString().padLeft(2, '0');
  final m = lastSeen.minute.toString().padLeft(2, '0');
  const months = [
    'Jan',
    'Feb',
    'Mar',
    'Apr',
    'May',
    'Jun',
    'Jul',
    'Aug',
    'Sep',
    'Oct',
    'Nov',
    'Dec',
  ];
  return '${months[lastSeen.month - 1]} ${lastSeen.day}, $h:$m';
}

enum TankStatus { healthy, ok, highTemp, lowTemp, offline, unknown }

TankStatus evaluateTankStatus(double? temp, bool isOnline) {
  if (!isOnline) {
    return TankStatus.offline;
  }
  if (temp == null) {
    return TankStatus.unknown;
  }
  if (temp > 28.0) {
    return TankStatus.highTemp;
  }
  if (temp < 18.0) {
    return TankStatus.lowTemp;
  }
  if (temp > 26.5) {
    return TankStatus.ok;
  }
  return TankStatus.healthy;
}
