import 'package:flex_color_scheme/flex_color_scheme.dart';
import 'package:flutter/material.dart';

// TankCtl color palette — dark indigo / soft periwinkle
class TankCtlColors {
  static const background  = Color(0xFF111128); // deep cool navy-indigo
  static const card        = Color(0xFF1C1A38); // dark indigo — 8 steps lighter
  static const primary     = Color(0xFF9D87F5); // soft periwinkle violet
  static const temperature = Color(0xFFE891C0); // muted orchid-pink — temp
  static const success     = Color(0xFF5BBFA0); // teal-mint — online
  static const warning     = Color(0xFFC9AEFF); // pale violet — light ON
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
        primaryContainer: Color(0xFF2D2460),
        secondary: TankCtlColors.success,
        secondaryContainer: Color(0xFF1A3D32),
        tertiary: TankCtlColors.warning,
        tertiaryContainer: Color(0xFF352A60),
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
