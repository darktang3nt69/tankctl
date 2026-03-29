---
title: Flutter App Architecture
type: reference
permalink: tankctl/frontend/flutter-app-architecture
tags:
- flutter
- frontend
- riverpod
---

## Flutter & Dart Architecture

### State Management
- **Riverpod** for reactive state management
- **GoRouter** for navigation and deep linking
- Providers for API calls and local state

### Key Directories
```
tankctl_app/lib/
├── providers/     # Riverpod state management
├── features/      # Feature-based modules
├── services/      # API/business logic
├── models/        # Data models
├── widgets/       # Reusable UI components
├── screens/       # Full-page screens
└── theme/         # Material Design 3 theming
```

### Design System
- **Material Design 3** compliance
- **Flex Color Scheme** for theming
- Dark/light mode support
- Responsive layout patterns

### Testing
- Unit tests with `test` package
- Widget tests for UI components
- Integration tests with `integration_test`
- Mock HTTP clients for API testing

### Build Outputs
- **Android:** APK & AAB builds
- **iOS:** IPA builds
- **Web:** Chrome deployment
- Firebase configuration for FCM

### Key Technologies
- `http` package for REST API calls
- `json_serializable` for data serialization
- `flutter_test` for testing framework
- Firebase SDK for push notifications