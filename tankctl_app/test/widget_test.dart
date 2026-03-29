// Basic smoke test: verifies the Material theme compiles and builds.
// Full app startup is NOT tested here because it requires Firebase init,
// live network calls, and timer cleanup that are out-of-scope for unit tests.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:tankctl_app/core/theme/app_theme.dart';

void main() {
  testWidgets('App theme builds without crashing', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        title: 'TankCTL',
        theme: AppTheme.light(),
        darkTheme: AppTheme.dark(),
        home: const Scaffold(body: Center(child: Text('TankCTL'))),
      ),
    );
    expect(find.text('TankCTL'), findsOneWidget);
    expect(find.byType(Scaffold), findsOneWidget);
  });
}
