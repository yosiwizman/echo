/// Centralized white-label branding configuration.
///
/// This file defines all brand-specific values for the Echo mobile app.
/// Modify these values to rebrand the application for different deployments.
class BrandingConfig {
  BrandingConfig._();

  /// Application display name
  static const String appName = 'Echo';

  /// Primary brand color (main theme color)
  /// Used for: app bars, buttons, primary UI elements
  static const int primaryColorValue = 0xFF000000; // Black

  /// Secondary brand color (accent color)
  /// Used for: highlights, secondary buttons, accents
  static const int secondaryColorValue = 0xFFFFFFFF; // White

  /// Logo asset path
  /// Update this to point to your custom logo
  static const String logoAssetPath = 'assets/images/herologo.png';

  /// App launcher icon path
  /// Used for generating platform-specific icons
  static const String launcherIconPath = 'assets/images/app_launcher_icon.png';

  /// App tagline/description
  static const String tagline = 'Your AI-powered wearable companion';

  // ==========================================
  // Platform-Specific Identifiers
  // ==========================================
  // Note: These are compile-time constants and cannot be changed at runtime.
  // They must match the values in android/app/build.gradle and ios/Runner/Info.plist
  // For a true white-label build, use flutter flavors or build-time code generation.

  /// Android package name / iOS bundle identifier
  /// This is for reference only - actual values are in platform config files
  static const String bundleIdentifier = 'com.yosiwizman.echo';

  // ==========================================
  // Usage Notes
  // ==========================================
  // 1. For simple rebrand: Update string/color values above
  // 2. For multiple brands: Consider using flavors (dev/prod/custom)
  // 3. For runtime config: Load from remote config service
  // 4. Update platform files separately:
  //    - Android: android/app/build.gradle
  //    - iOS: ios/Runner/Info.plist
}
