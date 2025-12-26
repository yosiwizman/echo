/// Application configuration.
///
/// Configure backend URL and other settings here.
class AppConfig {
  AppConfig._();

  /// Backend API base URL.
  ///
  /// For local development:
  /// - Android emulator: http://10.0.2.2:8000
  /// - iOS simulator: http://localhost:8000
  /// - Physical device: http://<your-ip>:8000
  static const String backendUrl = String.fromEnvironment(
    'BACKEND_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  /// App name.
  static const String appName = 'Echo';

  /// App version.
  static const String appVersion = '0.1.0';
}
