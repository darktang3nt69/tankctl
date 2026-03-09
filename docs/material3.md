Got it — you want a **clean, professional `.md` doc** (like the architecture docs you wrote for TankCtl) **and something you can directly give to Copilot / Cursor / AI coding agents** to implement. I’ll structure it properly with:

* clear sections
* commands
* folder structure
* code blocks
* implementation instructions for Copilot

This is **ready to drop into your repo**.

---

# `docs/flutter/material3.md`

```markdown
# Material 3 UI

## Overview

TankCtl mobile application uses **Flutter Material 3** as the base UI framework.

Material 3 provides:

- Modern UI components
- Native Android design language
- Built-in theming
- Accessibility support
- Adaptive layouts

Material 3 is included with Flutter and does **not require external dependencies**.

It will serve as the **foundation for all UI components** in the TankCtl mobile app.

---

# Why Material 3

Material 3 provides a **stable and scalable UI system** for the application.

Benefits:

- Native Flutter support
- Production ready
- High performance
- Consistent design system
- Easy integration with Flutter themes
- Works well with FlexColorScheme

Material 3 will power:

- Dashboard cards
- Control toggles
- Navigation
- Dialogs
- Layout components

---

# Design Philosophy

TankCtl mobile app follows a **dashboard-based UI**.

Main UI elements:

| Component | Purpose |
|-----------|--------|
Dashboard cards | Display device metrics |
Toggle switches | Control devices |
Navigation bar | Screen navigation |
Charts | Telemetry visualization |

The interface should be:

- Minimal
- Clean
- Dark-mode first
- Touch friendly

---

# App Structure

Flutter project layout:

```

tankctl_app/
│
├── lib/
│
├── core/
│   ├── theme/
│   └── constants/
│
├── features/
│   ├── dashboard/
│   ├── device/
│   ├── telemetry/
│   └── controls/
│
├── widgets/
│
└── main.dart

````

---

# Basic App Setup

Material 3 is enabled using the `useMaterial3` flag.

Example:

```dart
import 'package:flutter/material.dart';

void main() {
  runApp(const TankCtlApp());
}

class TankCtlApp extends StatelessWidget {
  const TankCtlApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "TankCtl",
      debugShowCheckedModeBanner: false,

      themeMode: ThemeMode.system,

      theme: ThemeData(
        useMaterial3: true,
      ),

      darkTheme: ThemeData.dark(
        useMaterial3: true,
      ),

      home: const Scaffold(
        body: Center(
          child: Text("TankCtl"),
        ),
      ),
    );
  }
}
````

---

# Core UI Components

## Card

Cards will be used for dashboard widgets.

Example:

```dart
Card(
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

## Switch (Light Control)

```dart
Switch(
  value: lightOn,
  onChanged: (value) {
    toggleLight(value);
  },
)
```

---

## NavigationBar

Bottom navigation for main screens.

```dart
NavigationBar(
  destinations: const [
    NavigationDestination(
      icon: Icon(Icons.dashboard),
      label: "Dashboard",
    ),
    NavigationDestination(
      icon: Icon(Icons.settings),
      label: "Settings",
    ),
  ],
)
```

---

# Layout Guidelines

Spacing rules:

| Element        | Size |
| -------------- | ---- |
| Screen padding | 16px |
| Card padding   | 16px |
| Widget spacing | 12px |

These values keep the UI visually balanced.

---

# Dark Mode

TankCtl mobile app defaults to **dark mode**.

Reason:

* IoT dashboards are easier to read in low light
* reduces battery usage
* better contrast for telemetry charts

Material 3 automatically adapts to dark mode.

Example:

```
themeMode: ThemeMode.system
```

---

# Responsibilities

Material 3 will provide:

* layout system
* component structure
* navigation
* interaction components

It does **not handle theming** beyond defaults.

Advanced theming will be handled by:

```
flex_color_scheme
```

---

# Next Step

After Material 3 setup the next dependency is:

```
flex_color_scheme
```

This will provide:

* custom color palettes
* improved dark mode
* polished dashboard UI

```