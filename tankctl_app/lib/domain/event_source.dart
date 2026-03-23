/// Event source types (Phase 3)
enum EventSource {
  device,
  app,
  backend,
  automation;

  String get displayName => switch (this) {
    EventSource.device => 'Device',
    EventSource.app => 'App',
    EventSource.backend => 'Backend',
    EventSource.automation => 'Automation',
  };

  String get label => name[0].toUpperCase() + name.substring(1);
}
