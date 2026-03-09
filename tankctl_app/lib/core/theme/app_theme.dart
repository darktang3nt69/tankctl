import 'package:flex_color_scheme/flex_color_scheme.dart';
import 'package:flutter/material.dart';

// TankCtl color palette — dark dashboard aesthetic
class TankCtlColors {
  static const background = Color(0xFF0F172A);
  static const card = Color(0xFF1E293B);
  static const primary = Color(0xFF38BDF8);
  static const temperature = Color(0xFFFB7185);
  static const success = Color(0xFF22C55E);
  static const warning = Color(0xFFF59E0B);
}

class AppTheme {
  static ThemeData light() {
    return FlexThemeData.light(
      scheme: FlexScheme.blue,
      useMaterial3: true,
      fontFamily: 'Roboto',
    );
  }

  static ThemeData dark() {
    return FlexThemeData.dark(
      colors: const FlexSchemeColor(
        primary: TankCtlColors.primary,
        primaryContainer: Color(0xFF0C4A6E),
        secondary: TankCtlColors.success,
        secondaryContainer: Color(0xFF14532D),
        tertiary: TankCtlColors.warning,
        tertiaryContainer: Color(0xFF78350F),
        appBarColor: TankCtlColors.background,
        error: TankCtlColors.temperature,
      ),
      scaffoldBackground: TankCtlColors.background,
      surfaceMode: FlexSurfaceMode.levelSurfacesLowScaffold,
      blendLevel: 10,
      useMaterial3: true,
      fontFamily: 'Roboto',
      subThemesData: const FlexSubThemesData(
        cardRadius: 12,
        defaultRadius: 10,
        cardElevation: 2,
        navigationBarBackgroundSchemeColor: SchemeColor.surface,
      ),
    );
  }
}
