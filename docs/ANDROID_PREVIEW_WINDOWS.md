# Echo Android Preview on Windows

This guide provides **exact, copy/paste steps** to run Echo on a Windows machine using Android Studio and an Android Emulator.

## Prerequisites

### System Requirements
- **Windows 10/11** (64-bit)
- **8GB RAM minimum** (16GB recommended for smooth emulator)
- **10GB free disk space** (for Android Studio + SDK + system images)
- **BIOS virtualization enabled** (Intel VT-x or AMD-V)

### Check Virtualization
```powershell
# Run in PowerShell as Administrator
Get-ComputerInfo | Select-Object HyperVisorPresent, HyperVRequirementVirtualizationFirmwareEnabled
```

If virtualization is disabled:
1. Restart PC → Enter BIOS (F2/F12/Del during boot)
2. Enable Intel VT-x or AMD-V
3. Save and reboot

## Required Windows Setting: Developer Mode (Flutter plugin symlinks)

Flutter uses **symlinks** for some plugins on Windows. If Windows Developer Mode is disabled, you may see:
- `Building with plugins requires symlink support`

Fix (recommended to do before anything else):
1. Settings → Privacy & security → For developers → **Developer Mode** → **On**
2. Re-run your Flutter command (`flutter pub get`, `flutter run`, etc.)

## Step 1: Install Flutter

### Option A: Direct Download (Recommended)
1. Download Flutter SDK: https://docs.flutter.dev/get-started/install/windows
2. Extract to `C:\src\flutter` (or any path without spaces)
3. Add to PATH:
   ```powershell
   # Add to User PATH
   $env:Path += ";C:\src\flutter\bin"
   [Environment]::SetEnvironmentVariable("Path", $env:Path, "User")
   ```
4. Verify:
   ```powershell
   flutter --version
   ```

### Option B: Using winget
```powershell
winget install --id=Google.Flutter -e
```

### Expected Flutter Version
Echo requires **Flutter 3.27.0+** (includes Dart 3.6.0+)

## Step 2: Install Android Studio

### Installation
```powershell
# Using winget (recommended)
winget install --id=Google.AndroidStudio -e

# Or download manually from:
# https://developer.android.com/studio
```

### First Launch Setup
1. Launch Android Studio
2. **Setup Wizard will start automatically**
3. Choose "Standard" installation
4. Click "Next" through all dialogs
5. Wait for downloads (~2-3 GB):
   - Android SDK
   - Android SDK Platform
   - Android SDK Build-Tools
   - Android Emulator
   - Intel x86 Emulator Accelerator (HAXM)

**This takes 15-30 minutes depending on internet speed.**

## Step 3: Configure Android SDK

### Verify SDK Installation
1. Open Android Studio
2. Click **More Actions** → **SDK Manager** (or **Tools** → **SDK Manager**)
3. **SDK Platforms** tab:
   - ✅ Check **Android 14.0 ("UpsideDownCake")** API Level 34
   - ✅ Check **Show Package Details** (bottom right)
   - Ensure **Android SDK Platform 34** is installed
4. **SDK Tools** tab:
   - ✅ Android SDK Build-Tools
   - ✅ Android SDK Command-line Tools
   - ✅ Android SDK Platform-Tools
   - ✅ Android Emulator
   - ✅ Intel x86 Emulator Accelerator (HAXM installer)
5. Click **Apply** if any are missing
6. Click **OK** when done

### Set Environment Variables
```powershell
# Add Android SDK to PATH
$androidSdk = "$env:LOCALAPPDATA\Android\Sdk"
$env:ANDROID_HOME = $androidSdk
$env:Path += ";$androidSdk\platform-tools"
$env:Path += ";$androidSdk\cmdline-tools\latest\bin"

# Persist for future sessions
[Environment]::SetEnvironmentVariable("ANDROID_HOME", $androidSdk, "User")
[Environment]::SetEnvironmentVariable("Path", $env:Path, "User")
```

### Verify SDK
```powershell
adb --version
# Should output: Android Debug Bridge version x.x.x
```

## Step 4: Create Android Virtual Device (AVD)

### Using Android Studio GUI
1. Open Android Studio
2. Click **More Actions** → **Virtual Device Manager**
3. Click **Create Device**
4. **Hardware:** Select **Pixel 6** (or Pixel 7/8)
5. Click **Next**
6. **System Image:** 
   - Select **UpsideDownCake** (API 34, Android 14.0)
   - Click **Download** if not installed (wait ~1GB download)
   - Select the downloaded image
7. Click **Next**
8. **AVD Name:** `Echo_Android_Emu` (EXACT name as specified)
9. **Startup orientation:** Portrait
10. Click **Show Advanced Settings**:
    - **RAM:** 2048 MB (or 4096 if you have 16GB+ system RAM)
    - **VM heap:** 512 MB
    - **Internal Storage:** 2048 MB
11. Click **Finish**

### Using Command Line (Alternative)
```powershell
# Create AVD
avdmanager create avd -n Echo_Android_Emu -k "system-images;android-34;google_apis;x86_64" -d "pixel_6"

# List AVDs
avdmanager list avd
```

## Step 5: Run Flutter Doctor

```powershell
cd C:\Users\<YourUsername>\echo
flutter doctor -v
```

### Expected Output
```
[✓] Flutter (Channel stable, 3.27.0, on Microsoft Windows...)
[✓] Windows Version (Installed version of Windows is version 10 or higher)
[✓] Android toolchain - develop for Android devices (Android SDK version 34.0.0)
[✓] Chrome - develop for the web
[✓] Visual Studio - develop Windows apps (Visual Studio Community...)
[✓] Android Studio (version 2023.x)
[✓] VS Code (version x.x.x)
[✓] Connected device (1 available)
[✓] Network resources
```

### Common Issues
**[!] Android toolchain - Android SDK not found:**
```powershell
flutter config --android-sdk $env:LOCALAPPDATA\Android\Sdk
```

**[!] Android Studio not found:**
```powershell
flutter config --android-studio-dir "C:\Program Files\Android\Android Studio"
```

**[!] cmdline-tools missing:**
- Open SDK Manager → SDK Tools → Install "Android SDK Command-line Tools"

## Step 6: Clone/Update Echo Repository

```powershell
# If not already cloned
git clone https://github.com/yosiwizman/echo.git
cd echo

# If already cloned
cd echo
git checkout main
git pull origin main
```

## Step 7: Install Dependencies

```powershell
cd apps\echo_mobile
flutter pub get
```

**Expected:** Downloads ~100+ packages (2-5 minutes first time)

### Verify pubspec
```powershell
# Check Flutter app name
Get-Content pubspec.yaml | Select-String "name:"
# Should show: name: echo_mobile
```

## Step 8: Launch Emulator

### Option A: Android Studio GUI
1. Open Android Studio
2. Click **More Actions** → **Virtual Device Manager**
3. Find `Echo_Android_Emu`
4. Click **▶ Play** button
5. Wait for emulator to boot (~30-60 seconds)

### Option B: Command Line (Faster)
```powershell
# List emulators
emulator -list-avds

# Launch Echo_Android_Emu
Start-Process emulator -ArgumentList "-avd", "Echo_Android_Emu"
```

### Verify Device
```powershell
flutter devices
```

**Expected output:**
```
2 connected devices:

Echo_Android_Emu (mobile) • emulator-5554 • android-x64 • Android 14 (API 34)
Chrome (web)              • chrome        • web-javascript • Google Chrome...
```

## Step 9: Run Echo

```powershell
# Ensure you're in the mobile app directory
cd C:\Users\<YourUsername>\echo\apps\echo_mobile

# Run in debug mode
flutter run
```

### What Happens
1. **Building...** (2-5 minutes first time)
   - Gradle downloads dependencies
   - Compiles Flutter app
   - Installs APK on emulator
2. **App launches on emulator**
3. **Hot reload enabled** - Press `r` to reload, `R` to restart, `q` to quit

### Expected First Launch
- ✅ **App icon visible** in emulator app drawer
- ✅ **Splash screen** shows briefly
- ✅ **Home screen** loads with navigation
- ✅ **No immediate crash**
- ⚠️ **Backend unavailable** warnings (EXPECTED - backend is optional for preview)

### Terminal Output
```
Launching lib\main.dart on Echo_Android_Emu in debug mode...
Running Gradle task 'assembleDebug'...
✓ Built build\app\outputs\flutter-apk\app-debug.apk.
Installing build\app\outputs\flutter-apk\app-debug.apk...
Syncing files to device Echo_Android_Emu...
Flutter run key commands.
r Hot reload.
R Hot restart.
h List all available interactive commands.
d Detach (terminate "flutter run" but leave application running).
c Clear the screen
q Quit (terminate the application on the device).

Running with sound null safety

An Observatory debugger and profiler on Echo_Android_Emu is available at: http://127.0.0.1:xxxxx
The Flutter DevTools debugger and profiler on Echo_Android_Emu is available at: http://127.0.0.1:xxxxx
```

## Step 10: Verify App Functionality

### Visual Verification
1. **Navigation:** Tap bottom navigation tabs (Home, Chat, Notes)
2. **UI loads:** Each screen shows content or empty state
3. **No crashes:** App remains stable
4. **Backend errors:** Accept as expected (optional backend)

### Test Hot Reload
1. Keep `flutter run` terminal open
2. Edit any .dart file (e.g., change a text string)
3. Press `r` in terminal
4. **Change appears instantly in emulator** (no rebuild)

## Common Issues & Fixes

### Issue: "No devices found"
**Fix:**
```powershell
# Check if emulator is running
adb devices

# If empty, launch emulator:
emulator -avd Echo_Android_Emu
```

### Issue: "Gradle build failed"
**Fix:**
```powershell
cd apps\echo_mobile\android
.\gradlew clean
cd ..\..
flutter clean
flutter pub get
flutter run
```

### Issue: "Unable to locate Android SDK"
**Fix:**
```powershell
flutter config --android-sdk $env:LOCALAPPDATA\Android\Sdk
flutter doctor --android-licenses
```

### Issue: "Emulator: Process finished with exit code 1"
**Fix:** HAXM acceleration issue
1. Open SDK Manager → SDK Tools
2. Install "Intel x86 Emulator Accelerator (HAXM installer)"
3. Navigate to: `C:\Users\<You>\AppData\Local\Android\Sdk\extras\intel\Hardware_Accelerated_Execution_Manager`
4. Run `intelhaxm-android.exe`
5. Restart PC

### Issue: "VT-x is not available"
**Fix:** Enable virtualization in BIOS (see Prerequisites section)

### Issue: App builds but doesn't launch
**Fix:**
```powershell
adb uninstall com.yosiwizman.echo
flutter clean
flutter run
```

### Issue: "Waiting for another flutter command to release the startup lock"
**Fix:**
```powershell
# Kill flutter processes
taskkill /F /IM dart.exe
taskkill /F /IM flutter.exe

# Delete lock file
Remove-Item "$env:LOCALAPPDATA\flutter\.flutter_tool_state.lock" -Force
```

## Build APK for Distribution

```powershell
cd apps\echo_mobile

# Build debug APK (for testing)
flutter build apk --debug

# Build release APK (for distribution)
flutter build apk --release

# Output location
ls build\app\outputs\flutter-apk\
```

**Files:**
- `app-debug.apk` (~40-50 MB)
- `app-release.apk` (~25-30 MB, optimized)

## Performance Tips

### Speed Up Emulator
1. Allocate more RAM (4GB if system allows)
2. Enable "Cold boot" instead of snapshot for fresh starts
3. Use x86_64 system images (faster than ARM)
4. Close other apps while developing

### Speed Up Builds
```powershell
# Enable Gradle daemon
$env:GRADLE_OPTS="-Dorg.gradle.daemon=true"

# Parallel builds
# Edit android\gradle.properties:
# org.gradle.parallel=true
# org.gradle.caching=true
```

## iOS Preview (macOS Required)

See:
- `docs/IOS_PREVIEW_MAC.md`

## Siri Shortcuts (iOS)

See:
- `docs/SIRI_SHORTCUTS_INTEGRATION.md`

---

## Summary

### Windows Android Preview - Complete ✅

**Flutter Version:** 3.27.0+ (Dart 3.6.0+)  
**Android API Level:** 34 (Android 14)  
**Emulator Name:** `Echo_Android_Emu`  
**Device:** Pixel 6

**Expected Result:**
- ✅ App launches on Android emulator
- ✅ UI is functional and navigable
- ✅ Hot reload works
- ⚠️ Backend errors are expected (optional service)

**Next Steps:**
1. Configure backend (optional) - see `docs/PREVIEW.md`
2. Test on physical Android device via USB debugging
3. Build release APK for distribution
4. iOS testing on macOS (see checklist above)

## Support

- **Full Preview Guide:** `docs/PREVIEW.md`
- **Architecture:** `docs/ARCHITECTURE.md`
- **Issues:** https://github.com/yosiwizman/echo/issues

---

*Last updated: Phase 6 (Windows Android + macOS iOS runbooks)*
