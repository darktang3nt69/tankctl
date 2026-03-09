Great — now we’ll move to the **next dependency doc** in the same clean style so you can drop it into your repo and give it to **Copilot / Cursor / Claude** to implement.

Next library:

**flex_color_scheme**

This will control **all colors of your app** and make the UI look **modern and polished**.

---

# `docs/flutter/flex_color_scheme.md`

````markdown
# FlexColorScheme Theme System

## Overview

TankCtl mobile app uses **flex_color_scheme** to manage application theming.

FlexColorScheme extends Flutter's Material 3 theming and provides:

- advanced color schemes
- consistent dark mode
- improved UI contrast
- modern dashboard aesthetics

This package is responsible for the **visual identity of the TankCtl mobile app**.

Material 3 provides the UI components, while FlexColorScheme defines **how the UI looks**.

---

# Installation

Add the dependency to `pubspec.yaml`.

```yaml
dependencies:
  flex_color_scheme: ^7.3.1
````

Install packages:

```
flutter pub get
```

---

# Design Goals

TankCtl mobile UI follows a **dark dashboard design** similar to:

* Home Assistant
* Tesla UI
* Grafana dashboards

Design principles:

* dark background
* high contrast cards
* accent colors for telemetry
* minimal visual noise

---

# TankCtl Color Palette

Primary UI colors:

| Element     | Color   |
| ----------- | ------- |
| Background  | #0F172A |
| Card        | #1E293B |
| Primary     | #38BDF8 |
| Temperature | #FB7185 |
| Success     | #22C55E |
| Warning     | #F59E0B |

These colors produce a **modern IoT dashboard look**.

---

# Theme Setup

FlexColorScheme is configured inside `main.dart`.

Example:

```dart
import 'package:flutter/material.dart';
import 'package:flex_color_scheme/flex_color_scheme.dart';

class TankCtlApp extends StatelessWidget {
  const TankCtlApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "TankCtl",
      debugShowCheckedModeBanner: false,

      themeMode: ThemeMode.system,

      theme: FlexThemeData.light(
        scheme: FlexScheme.blue,
        useMaterial3: true,
      ),

      darkTheme: FlexThemeData.dark(
        scheme: FlexScheme.blue,
        useMaterial3: true,
      ),

      home: const DashboardScreen(),
    );
  }
}
```

---

# Custom Theme Configuration

TankCtl uses a **custom dark theme** optimized for dashboards.

Example:

```dart
darkTheme: FlexThemeData.dark(
  colors: const FlexSchemeColor(
    primary: Color(0xFF38BDF8),
    secondary: Color(0xFF22C55E),
    appBarColor: Color(0xFF0F172A),
  ),
  scaffoldBackground: const Color(0xFF0F172A),
  surfaceMode: FlexSurfaceMode.levelSurfacesLowScaffold,
  blendLevel: 10,
  useMaterial3: true,
),
```

This produces:

* deep dark background
* elevated cards
* modern UI contrast

---

# UI Component Styling

## Dashboard Cards

Cards should appear slightly elevated.

Example:

```dart
Card(
  elevation: 2,
  child: Padding(
    padding: const EdgeInsets.all(16),
    child: Column(
      children: [
        Text("Temperature"),
        Text("24.5°C"),
      ],
    ),
  ),
)
```

---

# Accent Colors

Telemetry should use clear accent colors.

| Metric        | Color |
| ------------- | ----- |
| Temperature   | Red   |
| Device Online | Green |
| Warnings      | Amber |

Example:

```dart
Text(
  "24.5°C",
  style: TextStyle(
    color: Colors.redAccent,
    fontSize: 32,
  ),
)
```

---

# Theme Folder Structure

Create a dedicated theme module.

```
lib/
└── core/
    └── theme/
        └── app_theme.dart
```

Example:

```dart
class AppTheme {
  static ThemeData darkTheme = FlexThemeData.dark(
    scheme: FlexScheme.blue,
    useMaterial3: true,
  );
}
```

---

# Responsibilities

FlexColorScheme controls:

* app colors
* dark mode styling
* card elevation
* surface blending
* typography contrast

It does **not control business logic or widgets**.

---

# Next Step

Next dependency:

```
flutter_riverpod
```

Riverpod will manage application state such as:

* device status
* temperature telemetry
* light control state
* API responses

```

---

# How to Use This with Copilot / Cursor

Place the doc in your repo:

```

docs/flutter/flex_color_scheme.md

```

Then give Copilot this instruction:

```


