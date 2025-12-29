# Echo iOS Preview on macOS

This guide provides **exact, copy/paste steps** to run Echo on a macOS machine using Xcode + the iOS Simulator, and (optionally) on a physical iPhone.

If you are primarily trying to preview the UI quickly, start with Android on Windows:
- `docs/ANDROID_PREVIEW_WINDOWS.md`

If you want to complete Siri Shortcuts on iOS, see:
- `docs/SIRI_SHORTCUTS_INTEGRATION.md`

## What You Can / Can’t Test

- ✅ iOS Simulator: app launch + UI navigation + hot reload
- ✅ Physical iPhone: everything the simulator can do + device-only hardware checks
- ❌ Siri voice invocation (“Hey Siri, …”): **requires a physical iPhone**

## Prerequisites

### Required
- macOS 13+ (Ventura) recommended
- Xcode 15+ installed
- Flutter **3.27.0+** (Dart 3.6.0+)

### Recommended
- FVM (Flutter Version Manager) to match the repo’s pinned Flutter version
- CocoaPods (required for iOS builds with plugins)

## Step 0: Install Xcode + Command Line Tools

1. Install Xcode
   - App Store → **Xcode** → Install
   - Launch Xcode once after install

2. Install/confirm Command Line Tools

```bash
xcode-select --install
```

3. Accept Xcode license

```bash
sudo xcodebuild -license accept
```

4. Ensure Xcode is the selected developer directory

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
xcodebuild -version
```

5. In Xcode, set Command Line Tools:
   - Xcode → **Settings…** (or Preferences)
   - **Locations** → **Command Line Tools** → select the latest Xcode

## Step 1: Install Flutter (Recommended: FVM)

From a fresh terminal:

```bash
# Install fvm
dart pub global activate fvm

# In the repo root
cd ~/echo

# Install and use the pinned Flutter version
fvm install
fvm use

# Verify
fvm flutter --version
```

If you are NOT using FVM, verify:

```bash
flutter --version
```

## Step 2: Clone / Update Repo

```bash
# Clone
git clone https://github.com/yosiwizman/echo.git
cd echo

# Ensure main is up to date
git checkout main
git pull origin main
```

## Step 3: Get Flutter Dependencies

```bash
cd apps/echo_mobile

# With FVM
fvm flutter pub get

# Without FVM
# flutter pub get
```

## Step 4: Install CocoaPods + iOS Pods

### 4.1 Install CocoaPods (one-time)

Option A (Homebrew):

```bash
brew install cocoapods
```

Option B (RubyGems):

```bash
sudo gem install cocoapods
```

Verify:

```bash
pod --version
```

### 4.2 Install Pods for this repo

```bash
cd ios
pod install
cd ..
```

**Important:** `pod install` should create `ios/Runner.xcworkspace`.

## Step 5: Run on iOS Simulator

1. Start the simulator

```bash
open -a Simulator
```

2. Verify Flutter sees the simulator

```bash
cd ~/echo/apps/echo_mobile
fvm flutter devices
```

3. Run

```bash
# From apps/echo_mobile
fvm flutter run
```

Expected:
- Xcode build runs
- The app launches on the simulator
- Hot reload works (`r` in the terminal)

## Step 6: Run on a Physical iPhone (Optional)

### 6.1 Connect and trust
1. Plug in iPhone via USB
2. Unlock iPhone → tap **Trust**
3. In Xcode: Window → **Devices and Simulators** → confirm the device appears

### 6.2 Fix code signing (if needed)
If `flutter run` fails with signing errors:
1. Open:

```bash
open ios/Runner.xcworkspace
```

2. In Xcode:
   - Select **Runner** project (left sidebar)
   - Select **Runner** target
   - Signing & Capabilities → select a **Team**
   - Keep “Automatically manage signing” enabled

If Xcode complains the bundle ID is not available, set a unique one locally (do not commit):
- `apps/echo_mobile/ios/Flutter/Base.xcconfig` → update `APP_BUNDLE_IDENTIFIER=`

### 6.3 Run on device

```bash
cd ~/echo/apps/echo_mobile
fvm flutter devices
fvm flutter run -d <YOUR_DEVICE_ID>
```

## Siri Shortcuts (iOS) — Completion

Siri Shortcuts are **not fully complete in the repo** without Xcode GUI steps.
Follow:
- `docs/SIRI_SHORTCUTS_INTEGRATION.md` → “macOS / Xcode completion checklist”

## Common Issues & Fixes

### Issue: `flutter doctor` shows Xcode errors

```bash
fvm flutter doctor -v
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

### Issue: CocoaPods “sandbox is not in sync”

```bash
cd ios
pod install
cd ..
```

### Issue: Pods / build failures after dependency changes

```bash
cd ios
rm -rf Pods Podfile.lock
pod install
cd ..

fvm flutter clean
fvm flutter pub get
fvm flutter run
```

### Issue: “No devices found” (simulator)
- Ensure Xcode is installed and opened once
- Ensure the simulator app is running: `open -a Simulator`
- Re-run: `fvm flutter devices`
