# Echo Local Preview Guide

This guide explains how to run and preview the Echo mobile application locally on your development machine.

## What is Echo?

Echo is an **AI-powered wearable companion mobile application** built with Flutter. It provides:
- Real-time voice interaction
- Intelligent note-taking
- Automated action execution
- Integration with wearable devices

**Platform:** Native mobile app (Android + iOS)  
**Framework:** Flutter 3.27.0 with Dart 3.6.0  
**Backend:** FastAPI (optional for preview)

## Prerequisites

Before running Echo locally, ensure you have:

### Required
- **Flutter SDK 3.27.0+** ([Install Flutter](https://docs.flutter.dev/get-started/install))
- **Git** (for cloning the repository)
- **An emulator/simulator or physical device:**
  - **Android:** Android Studio + Android Emulator (or physical device with USB debugging)
  - **iOS:** macOS + Xcode + iOS Simulator (or physical device)

### Recommended
- **FVM (Flutter Version Manager)** for deterministic Flutter versioning
- **VS Code** or **Android Studio** with Flutter plugin

### Check Your Setup
```bash
flutter doctor
```

This command validates your Flutter installation and shows missing dependencies.

## Quick Start

### 1. Clone the Repository

```bash
git checkout https://github.com/yosiwizman/echo.git
cd echo
```

### 2. Navigate to Mobile App

```bash
cd apps/echo_mobile
```

### 3. Install Flutter Version (if using FVM)

The repository includes `.fvmrc` specifying Flutter 3.27.0:

```bash
# Install FVM if you haven't already
dart pub global activate fvm

# Install and use the pinned Flutter version
fvm install
fvm use

# Verify version
fvm flutter --version
```

### 4. Get Dependencies

```bash
# With FVM
fvm flutter pub get

# Without FVM
flutter pub get
```

This downloads all required Flutter packages (~2-3 minutes on first run).

### 5. Run on Emulator/Simulator

#### Android Emulator

```bash
# List available devices
flutter devices

# Run on Android
fvm flutter run  # or: flutter run
```

**First-time Android setup:**
1. Open Android Studio
2. AVD Manager → Create Virtual Device
3. Select Pixel 6 (or similar), API 34 (Android 14)
4. Start the emulator
5. Run `flutter run`

#### iOS Simulator (macOS only)

```bash
# Start simulator
open -a Simulator

# Run on iOS
fvm flutter run  # or: flutter run
```

**First-time iOS setup:**
1. Install Xcode from App Store
2. `xcode-select --install` (command line tools)
3. `sudo xcodebuild -license accept`
4. Open Xcode → Preferences → Locations → ensure Command Line Tools is set
5. Run `flutter run`

### 6. Run on Physical Device

#### Android (USB Debugging)
1. Enable Developer Options on your Android device
2. Enable USB Debugging
3. Connect via USB
4. `flutter devices` (should show your device)
5. `flutter run`

#### iOS (Mac + iPhone)
1. Connect iPhone via USB
2. Xcode → Window → Devices and Simulators
3. Trust the device
4. `flutter devices`
5. `flutter run`

## Expected First-Run Behavior

### App Launch
- **Splash screen:** Echo logo with loading indicator
- **Home screen:** Navigation tabs (Home, Chat, Notes)
- **Initial state:** Empty state messages (no conversations/notes yet)

### Without Backend
If the Echo backend is not running:
- App will launch successfully
- UI navigation works
- API calls will fail gracefully with error messages
- Chat and notes features will show "Backend unavailable"

This is **expected behavior** for local preview mode.

### With Backend (Optional)
To test full functionality:

```bash
# In a separate terminal
cd services/echo_backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Update backend URL in `lib/config/app_config.dart` if needed.

## Common Issues & Fixes

### Issue: `flutter: command not found`
**Fix:** Flutter is not in your PATH. Reinstall Flutter or update PATH manually.

### Issue: `No devices found`
**Fix:**
- Android: Start an emulator via Android Studio AVD Manager
- iOS: `open -a Simulator`
- Check: `flutter devices`

### Issue: `Gradle build failed` (Android)
**Fix:**
```bash
cd android
./gradlew clean
cd ..
flutter clean
flutter pub get
flutter run
```

### Issue: `Xcode build failed` (iOS)
**Fix:**
```bash
cd ios
rm -rf Pods Podfile.lock
pod install
cd ..
flutter clean
flutter run
```

### Issue: `Version solving failed` (dependencies)
**Fix:** Ensure you're using Flutter 3.27.0:
```bash
flutter --version
fvm use  # if using FVM
flutter pub get
```

### Issue: `MissingPluginException`
**Fix:**
```bash
flutter clean
flutter pub get
# Then do a full rebuild (not hot reload)
flutter run
```

## Development Workflow

### Hot Reload
While the app is running:
- **Hot reload:** Press `r` in the terminal (fast, preserves state)
- **Hot restart:** Press `R` (full restart, resets state)
- **Quit:** Press `q`

### Build Modes
```bash
# Debug mode (default, with hot reload)
flutter run

# Profile mode (performance testing)
flutter run --profile

# Release mode (optimized, no debugging)
flutter run --release
```

## Build for Distribution

### Android APK
```bash
flutter build apk --release
# Output: build/app/outputs/flutter-apk/app-release.apk
```

### iOS Archive (Mac only)
```bash
flutter build ios --release
# Then use Xcode to create IPA for TestFlight/App Store
```

## Platform Recommendation

### Best for First Visual Review
**Android Emulator** is recommended for initial preview:
- ✅ Works on Windows, macOS, Linux
- ✅ Faster setup than iOS
- ✅ Easier device debugging
- ✅ No Apple Developer account needed

**iOS Simulator** (macOS only):
- Better visual fidelity
- Required for App Store submission testing
- Requires Xcode (large download)

### Recommendation
1. **Start with Android emulator** for rapid iteration
2. **Test on iOS simulator** before release
3. **Test on physical devices** for final validation

## What Remains Before Store Release

### Before TestFlight (iOS)
- [ ] Apple Developer account ($99/year)
- [ ] App Store Connect setup
- [ ] Bundle identifier configuration
- [ ] Provisioning profiles and certificates
- [ ] App icon and screenshots
- [ ] Privacy policy URL
- [ ] TestFlight beta testing

### Before Play Store (Android)
- [ ] Google Play Console account ($25 one-time)
- [ ] App signing key generation
- [ ] Store listing (screenshots, description)
- [ ] Content rating questionnaire
- [ ] Privacy policy URL
- [ ] Internal testing track

### Technical Requirements
- [ ] Backend deployed and accessible (not localhost)
- [ ] Firebase project configured (auth, analytics)
- [ ] API keys configured (OpenAI, Deepgram, etc.)
- [ ] Push notifications setup
- [ ] Crash reporting enabled
- [ ] Performance monitoring
- [ ] End-to-end testing complete
- [ ] User acceptance testing (UAT)

### Compliance
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] GDPR compliance (if EU users)
- [ ] COPPA compliance (if <13 users)
- [ ] Accessibility testing

## Support

- **Documentation:** See `README.md` and `docs/ARCHITECTURE.md`
- **Issues:** https://github.com/yosiwizman/echo/issues
- **CI Status:** https://github.com/yosiwizman/echo/actions

---

*Last updated: Phase 3 (Local Preview Build)*
