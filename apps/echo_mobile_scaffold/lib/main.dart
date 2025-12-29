import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:echo_mobile/config/app_config.dart';
import 'package:echo_mobile/services/api_service.dart';
import 'package:echo_mobile/screens/app_shell.dart';

void main() {
  runApp(const EchoApp());
}

class EchoApp extends StatelessWidget {
  const EchoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Provider<ApiService>(
      create: (_) => ApiService(baseUrl: AppConfig.backendUrl),
      child: MaterialApp(
        title: 'Echo',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.deepPurple,
            brightness: Brightness.light,
          ),
          useMaterial3: true,
        ),
        darkTheme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.deepPurple,
            brightness: Brightness.dark,
          ),
          useMaterial3: true,
        ),
        themeMode: ThemeMode.system,
        home: const AppShell(),
      ),
    );
  }
}
