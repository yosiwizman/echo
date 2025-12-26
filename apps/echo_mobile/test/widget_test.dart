import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:echo_mobile/services/api_service.dart';
import 'package:echo_mobile/screens/home_screen.dart';

void main() {
  // Ensure Flutter test bindings are initialized
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Home screen shows Echo title', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Provider<ApiService>(
          create: (_) => ApiService(baseUrl: 'http://localhost:8000'),
          child: const HomeScreen(),
        ),
      ),
    );

    // Pump a frame to allow initial build
    await tester.pump();

    expect(find.text('Echo'), findsWidgets);
    expect(find.text('Start Session'), findsOneWidget);
  });

  testWidgets('Home screen has start session button', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Provider<ApiService>(
          create: (_) => ApiService(baseUrl: 'http://localhost:8000'),
          child: const HomeScreen(),
        ),
      ),
    );

    // Pump a frame to allow initial build
    await tester.pump();

    // Use key-based lookup for stability across UI refactors
    final button = find.byKey(const Key('start_session_button'));
    expect(button, findsOneWidget);
  });
}
