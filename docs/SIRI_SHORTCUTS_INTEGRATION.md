# Echo Siri Shortcuts Integration - Minimal Implementation

## Audit Results: Existing Capture Entry Points

### ✅ Found Entry Points (No New Architecture Needed)

#### 1. **Main Capture Screen**
- **Route:** `ConversationCapturingPage` (`lib/pages/conversation_capturing/page.dart`)
- **Navigation:** Accessed from HomePage when device is connected
- **State:** Uses existing `CaptureProvider`

#### 2. **Capture Provider Methods** (`lib/providers/capture_provider.dart`)

| Method | Purpose | Use Case |
|--------|---------|----------|
| `streamRecording()` | Start phone mic recording | AirPods/headphones mode |
| `stopStreamRecording()` | Stop phone mic recording | End session |
| `streamDeviceRecording({BtDevice?})` | Start device (Omi) recording | Hardware device mode |
| `stopStreamDeviceRecording()` | Stop device recording | End device session |
| `streamSystemAudioRecording()` | Desktop system audio | macOS/Windows only |
| `pauseDeviceRecording()` | Pause current recording | Mute functionality |
| `resumeDeviceRecording()` | Resume paused recording | Unmute functionality |

#### 3. **Recording States** (`RecordingState` enum)
```dart
enum RecordingState {
  initialising,
  record,
  deviceRecord,
  systemAudioRecord,
  pause,
  stop,
}
```

#### 4. **Voice Recorder Widget**
- **File:** `lib/pages/chat/widgets/voice_recorder_widget.dart`
- **Methods:** `startListening()`, `stopListening()`
- **Context:** Chat interface voice input

---

## Proposed Siri Shortcuts Integration

### Approach: **Zero New Architecture**
Connect iOS Siri Shortcuts → existing `CaptureProvider` methods via method channel.

---

## Implementation Plan

### Phase 1: iOS Siri Shortcuts Bridge (Required)

#### 1.1 Add Siri Intents Definition (`ios/Runner/Intents.intentdefinition`)

Create Xcode Intents file with 3 shortcuts:

| Shortcut Phrase | Intent Name | Parameters | Target Action |
|----------------|-------------|------------|---------------|
| "Open Echo" | OpenEchoIntent | None | Launch app → HomePage |
| "Start Echo" | StartEchoIntent | None | Launch app → Navigate to ConversationCapturingPage → Call `streamRecording()` |
| "Stop Echo" | StopEchoIntent | None | Foreground app → Call `stopStreamRecording()` |

#### 1.2 Update `Info.plist`

```xml
<!-- Add to ios/Runner/Info.plist -->
<key>NSSiriUsageDescription</key>
<string>Echo uses Siri for hands-free voice activation when using AirPods or headphones.</string>

<key>NSMicrophoneUsageDescription</key>
<string>Echo needs microphone access to record your voice conversations.</string>

<key>NSBluetoothAlwaysUsageDescription</key>
<string>Echo connects to your Bluetooth headphones for voice capture.</string>

<key>NSSupportsLiveActivities</key>
<true/>
```

#### 1.3 Create Intent Handler (`ios/Runner/IntentHandler.swift`)

```swift
import Intents
import UIKit

class IntentHandler: INExtension, OpenEchoIntentHandling, StartEchoIntentHandling, StopEchoIntentHandling {
    
    // MARK: - OpenEchoIntent (Just launch app)
    func handle(intent: OpenEchoIntent, completion: @escaping (OpenEchoIntentResponse) -> Void) {
        // iOS will bring app to foreground automatically
        completion(OpenEchoIntentResponse(code: .success, userActivity: nil))
    }
    
    // MARK: - StartEchoIntent (Launch + Start Recording)
    func handle(intent: StartEchoIntent, completion: @escaping (StartEchoIntentResponse) -> Void) {
        // Post notification to Flutter via NotificationCenter
        NotificationCenter.default.post(
            name: NSNotification.Name("EchoStartRecording"),
            object: nil,
            userInfo: ["source": "siri_shortcut"]
        )
        
        completion(StartEchoIntentResponse(code: .success, userActivity: nil))
    }
    
    // MARK: - StopEchoIntent (Stop Recording)
    func handle(intent: StopEchoIntent, completion: @escaping (StopEchoIntentResponse) -> Void) {
        NotificationCenter.default.post(
            name: NSNotification.Name("EchoStopRecording"),
            object: nil
        )
        
        completion(StopEchoIntentResponse(code: .success, userActivity: nil))
    }
}
```

#### 1.4 Update `AppDelegate.swift`

```swift
// Add to AppDelegate.swift didFinishLaunchingWithOptions:

// Setup Siri Shortcuts notification listeners
NotificationCenter.default.addObserver(
    self,
    selector: #selector(handleStartRecordingShortcut),
    name: NSNotification.Name("EchoStartRecording"),
    object: nil
)

NotificationCenter.default.addObserver(
    self,
    selector: #selector(handleStopRecordingShortcut),
    name: NSNotification.Name("EchoStopRecording"),
    object: nil
)

// Add methods to AppDelegate:

@objc private func handleStartRecordingShortcut(notification: Notification) {
    guard let controller = window?.rootViewController as? FlutterViewController else { return }
    
    let methodChannel = FlutterMethodChannel(
        name: "com.echo/siri_shortcuts",
        binaryMessenger: controller.binaryMessenger
    )
    
    methodChannel.invokeMethod("startRecording", arguments: ["source": "siri"])
}

@objc private func handleStopRecordingShortcut(notification: Notification) {
    guard let controller = window?.rootViewController as? FlutterViewController else { return }
    
    let methodChannel = FlutterMethodChannel(
        name: "com.echo/siri_shortcuts",
        binaryMessenger: controller.binaryMessenger
    )
    
    methodChannel.invokeMethod("stopRecording", arguments: nil)
}
```

---

### Phase 2: Flutter Method Channel Listener (Required)

#### 2.1 Create Siri Shortcuts Service (`lib/services/siri_shortcuts_service.dart`)

```dart
import 'package:flutter/services.dart';
import 'package:omi/providers/capture_provider.dart';
import 'package:omi/utils/logger.dart';

class SiriShortcutsService {
  static const MethodChannel _channel = MethodChannel('com.echo/siri_shortcuts');
  final CaptureProvider _captureProvider;
  
  SiriShortcutsService(this._captureProvider) {
    _channel.setMethodCallHandler(_handleMethod);
  }
  
  Future<void> _handleMethod(MethodCall call) async {
    try {
      switch (call.method) {
        case 'startRecording':
          await _handleStartRecording(call.arguments);
          break;
        case 'stopRecording':
          await _handleStopRecording();
          break;
        default:
          Logger.info('Unknown Siri Shortcut method: ${call.method}');
      }
    } catch (e) {
      Logger.error('Siri Shortcut error: $e');
    }
  }
  
  Future<void> _handleStartRecording(dynamic arguments) async {
    Logger.info('Siri Shortcut: Start Recording (source: ${arguments?['source']})');
    
    // Use existing CaptureProvider method - NO NEW LOGIC
    if (_captureProvider.recordingState == RecordingState.stop) {
      await _captureProvider.streamRecording();
      Logger.info('Recording started via Siri');
    } else {
      Logger.warn('Recording already active, ignoring Siri command');
    }
  }
  
  Future<void> _handleStopRecording() async {
    Logger.info('Siri Shortcut: Stop Recording');
    
    // Use existing CaptureProvider method - NO NEW LOGIC
    if (_captureProvider.recordingState == RecordingState.record) {
      await _captureProvider.stopStreamRecording();
      Logger.info('Recording stopped via Siri');
    } else {
      Logger.warn('No active recording to stop');
    }
  }
}
```

#### 2.2 Register Service in Main App (`lib/main.dart`)

```dart
// Add after CaptureProvider initialization:

final captureProvider = Provider.of<CaptureProvider>(context, listen: false);
final siriShortcutsService = SiriShortcutsService(captureProvider);
```

---

### Phase 3: Optional UX Enhancement (Minimal)

#### 3.1 Headset Mode Indicator Widget (`lib/widgets/headset_mode_indicator.dart`)

```dart
import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';

class HeadsetModeIndicator extends StatelessWidget {
  final bool isHeadsetConnected;
  
  const HeadsetModeIndicator({super.key, required this.isHeadsetConnected});
  
  @override
  Widget build(BuildContext context) {
    if (!isHeadsetConnected) return const SizedBox.shrink();
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.blue.withOpacity(0.2),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.blue, width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const FaIcon(FontAwesomeIcons.headphones, size: 14, color: Colors.blue),
          const SizedBox(width: 6),
          Text(
            'Headset Mode',
            style: TextStyle(
              fontSize: 12,
              color: Colors.blue[700],
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}
```

#### 3.2 Detect Bluetooth Audio (Platform Service)

```dart
// Add to lib/utils/platform/platform_service.dart or create new file:

import 'package:flutter/services.dart';

class AudioRouteService {
  static const MethodChannel _channel = MethodChannel('com.echo/audio_route');
  
  static Future<bool> isBluetoothHeadsetConnected() async {
    try {
      final result = await _channel.invokeMethod('isBluetoothConnected');
      return result ?? false;
    } catch (e) {
      return false;
    }
  }
  
  static Stream<bool> headsetConnectionStream() {
    return _channel.invokeMethod('observeAudioRoute').asStream().cast<bool>();
  }
}
```

#### 3.3 iOS Native Audio Route Detection (`ios/Runner/AudioRouteObserver.swift`)

```swift
import AVFoundation

class AudioRouteObserver {
    static let shared = AudioRouteObserver()
    private var methodChannel: FlutterMethodChannel?
    
    func setup(binaryMessenger: FlutterBinaryMessenger) {
        methodChannel = FlutterMethodChannel(
            name: "com.echo/audio_route",
            binaryMessenger: binaryMessenger
        )
        
        methodChannel?.setMethodCallHandler { [weak self] call, result in
            switch call.method {
            case "isBluetoothConnected":
                result(self?.isBluetoothAudioConnected() ?? false)
            default:
                result(FlutterMethodNotImplemented)
            }
        }
        
        // Listen for audio route changes
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(audioRouteChanged),
            name: AVAudioSession.routeChangeNotification,
            object: nil
        )
    }
    
    private func isBluetoothAudioConnected() -> Bool {
        let audioSession = AVAudioSession.sharedInstance()
        let outputs = audioSession.currentRoute.outputs
        
        for output in outputs {
            if output.portType == .bluetoothA2DP || 
               output.portType == .bluetoothLE ||
               output.portType == .bluetoothHFP {
                return true
            }
        }
        return false
    }
    
    @objc private func audioRouteChanged(notification: Notification) {
        let isConnected = isBluetoothAudioConnected()
        methodChannel?.invokeMethod("audioRouteChanged", arguments: isConnected)
    }
}
```

#### 3.4 Add Indicator to ConversationCapturingPage

```dart
// In lib/pages/conversation_capturing/page.dart, add to AppBar:

FutureBuilder<bool>(
  future: AudioRouteService.isBluetoothHeadsetConnected(),
  builder: (context, snapshot) {
    return HeadsetModeIndicator(
      isHeadsetConnected: snapshot.data ?? false,
    );
  },
),
```

---

## What Is NOT Implemented (Intentionally Deferred)

### ❌ Not Adding:
1. **New state machines** - Using existing `CaptureProvider` states
2. **New session managers** - Omni already has comprehensive session logic
3. **BLE button logic** - Omni device already handles this natively
4. **Background recording** - App Store policy violation
5. **Always-on listening** - Not in V1, requires special entitlements
6. **Custom audio processing** - iOS AVAudioSession handles routing
7. **Wake word detection** - Deferred to future
8. **Health vitals** - Not in V1

### ✅ Reusing Omni:
- Existing transcription pipeline
- Existing WebSocket connections
- Existing conversation state management
- Existing audio capture/playback
- Existing BLE device handling
- Existing permission flows

---

## Testing Checklist

### Siri Shortcuts Testing (iOS Device Required)

1. **Install & Register Shortcuts**
   - [ ] Build iOS app with new intents
   - [ ] Open Settings → Siri & Search → "Echo"
   - [ ] Verify 3 shortcuts appear: "Open Echo", "Start Echo", "Stop Echo"

2. **Test "Open Echo"**
   - [ ] Lock iPhone
   - [ ] Say "Hey Siri, Open Echo"
   - [ ] Verify app launches to HomePage

3. **Test "Start Echo"**
   - [ ] Lock iPhone with AirPods connected
   - [ ] Say "Hey Siri, Start Echo"
   - [ ] Verify app launches
   - [ ] Verify ConversationCapturingPage opens
   - [ ] Verify recording starts (mic permission granted)
   - [ ] Speak into AirPods mic
   - [ ] Verify transcription appears

4. **Test "Stop Echo"**
   - [ ] While recording active
   - [ ] Say "Hey Siri, Stop Echo"
   - [ ] Verify recording stops
   - [ ] Verify conversation is processed

5. **Test Headset Indicator**
   - [ ] Connect AirPods
   - [ ] Open ConversationCapturingPage
   - [ ] Verify "Headset Mode" indicator appears
   - [ ] Disconnect AirPods
   - [ ] Verify indicator disappears

6. **Test Permission Flows**
   - [ ] Fresh install → Siri permission prompt
   - [ ] First "Start Echo" → Microphone permission prompt
   - [ ] Deny microphone → Verify graceful error

---

## Files to Create/Modify

### New Files (5):
1. `ios/Runner/Intents.intentdefinition` (Xcode file)
2. `ios/Runner/IntentHandler.swift`
3. `lib/services/siri_shortcuts_service.dart`
4. `lib/widgets/headset_mode_indicator.dart`
5. `ios/Runner/AudioRouteObserver.swift`

### Modified Files (3):
1. `ios/Runner/Info.plist` (add Siri usage strings)
2. `ios/Runner/AppDelegate.swift` (add notification observers)
3. `lib/main.dart` (register SiriShortcutsService)

### Optional Modifications (1):
1. `lib/pages/conversation_capturing/page.dart` (add headset indicator)

---

## Estimated Effort

| Task | Lines of Code | Time Estimate |
|------|---------------|---------------|
| iOS Intents Definition | ~50 (Xcode GUI) | 30 min |
| IntentHandler.swift | ~80 | 1 hour |
| AppDelegate updates | ~40 | 30 min |
| SiriShortcutsService.dart | ~70 | 1 hour |
| HeadsetModeIndicator.dart | ~40 | 30 min |
| AudioRouteObserver.swift | ~60 | 1 hour |
| Testing on device | N/A | 2 hours |

**Total:** ~340 lines of code, ~6.5 hours

---

## Known Blockers & Fixes

### Blocker 1: "Cannot test on iOS Simulator"
**Reason:** Siri Shortcuts require physical iPhone  
**Fix:** Must test on real device with iOS 15+

### Blocker 2: "Microphone permission denied"
**Reason:** User declined permission  
**Fix:** Show alert directing to Settings app (already handled by Omni)

### Blocker 3: "Shortcut doesn't appear in Siri Settings"
**Reason:** Intents not properly registered  
**Fix:** Clean build, delete app, reinstall

### Blocker 4: "Audio not routed to AirPods"
**Reason:** AVAudioSession misconfigured  
**Fix:** Omni already configures this correctly - no changes needed

### Blocker 5: "Recording starts but no transcription"
**Reason:** Backend not connected  
**Fix:** Check WebSocket connection (existing Omni debug flow)

---

## Migration from Phase 1 Branch

Since the Omni white-label code is on `phase-1-omi-white-label`, you need to:

1. **Merge Phase 1 to main:**
   ```bash
   git checkout main
   git merge phase-1-omi-white-label
   ```

2. **OR work directly on Phase 1 branch:**
   ```bash
   git checkout phase-1-omi-white-label
   # Make Siri Shortcuts changes here
   ```

3. **Create new feature branch:**
   ```bash
   git checkout -b feature/siri-shortcuts-integration phase-1-omi-white-label
   # Implement changes
   ```

---

## ⚠️ WINDOWS PARTIAL IMPLEMENTATION - MACOS COMPLETION REQUIRED

### What Was Implemented on Windows (✅ Complete)

**Flutter/Dart Code:**
- ✅ `lib/services/siri_shortcuts_service.dart` - MethodChannel bridge to CaptureProvider
- ✅ `lib/main.dart` - Service initialization in app lifecycle
- ✅ Defensive checks (don't start if recording, don't stop if idle)
- ✅ Structured logging with activation source tracking

**iOS Swift Code:**
- ✅ `ios/Runner/IntentHandler.swift` - Placeholder intent handlers
- ✅ `ios/Runner/AppDelegate.swift` - NotificationCenter observers + MethodChannel bridge
- ✅ `ios/Runner/Info.plist` - NSSiriUsageDescription added

**Documentation:**
- ✅ Complete implementation guide
- ✅ Testing checklist
- ✅ macOS completion steps (below)

---

## 🍎 macOS Completion Checklist (Missing 20%)

### Prerequisites
- macOS 12+ (Monterey or later)
- Xcode 14+ installed
- Physical iPhone with iOS 15+ (Simulator cannot test Siri)
- Apple Developer account (for Siri entitlement)

### Step 1: Open Project in Xcode

```bash
cd ~/echo/apps/echo_mobile
open ios/Runner.xcworkspace
```

**⚠️ Important:** Open `.xcworkspace`, NOT `.xcodeproj`

### Step 2: Create Intents.intentdefinition File

1. In Xcode Project Navigator (left sidebar):
   - Right-click on `Runner` folder
   - Select **New File...**
   - Choose **SiriKit Intent Definition File**
   - Name: `Intents.intentdefinition`
   - Target: ✅ Runner
   - Click **Create**

2. Select `Intents.intentdefinition` in Project Navigator

3. Click **➕ (plus)** at bottom left → **New Intent**

4. **Create StartEchoIntent:**
   - Intent Name: `StartEchoIntent`
   - Category: `Play`
   - Title: `Start Echo`
   - Description: `Start recording with Echo`
   - Confirmation: ❌ (unchecked)
   - Supported: ✅ `Siri`
   - Response: Leave default

5. Click **➕** again → **New Intent**

6. **Create StopEchoIntent:**
   - Intent Name: `StopEchoIntent`
   - Category: `Pause`
   - Title: `Stop Echo`
   - Description: `Stop recording with Echo`
   - Confirmation: ❌ (unchecked)
   - Supported: ✅ `Siri`
   - Response: Leave default

### Step 3: Update IntentHandler.swift

Replace placeholder code in `ios/Runner/IntentHandler.swift`:

```swift
// Replace this section:
override func handler(for intent: INIntent) -> Any {
    if intent is INStartWorkoutIntent {  // OLD
        return StartEchoIntentHandler()
    } else if intent is INPauseWorkoutIntent {  // OLD
        return StopEchoIntentHandler()
    }
    return self
}

// With this:
override func handler(for intent: INIntent) -> Any {
    if intent is StartEchoIntent {  // NEW - generated from intentdefinition
        return StartEchoIntentHandler()
    } else if intent is StopEchoIntent {  // NEW - generated from intentdefinition
        return StopEchoIntentHandler()
    }
    return self
}
```

**Note:** `StartEchoIntent` and `StopEchoIntent` classes will be auto-generated by Xcode.

### Step 4: Add Siri Capability

1. In Xcode, select **Runner** (top of Project Navigator)
2. Select **Runner** target
3. Click **Signing & Capabilities** tab
4. Click **➕ Capability**
5. Search for and add **Siri**
6. Ensure your Apple Developer team is selected in **Signing**

### Step 5: Build and Run

1. Connect physical iPhone via USB
2. Select iPhone as target device (top toolbar)
3. Click **▶ Run** or press `Cmd+R`
4. Wait for build to complete (~2-5 minutes first time)
5. App should install and launch on iPhone

### Step 6: Register Shortcuts with Siri

**On iPhone:**

1. Open **Settings** app
2. Go to **Siri & Search**
3. Scroll down to find **Echo** app
4. Tap **Echo**
5. You should see:
   - "Start Echo"
   - "Stop Echo"
6. Tap each to add custom phrase or use default

**Alternative:** First time you say "Hey Siri, Start Echo", Siri will ask to enable the shortcut.

### Step 7: Test on Physical iPhone

#### Test 1: "Open Echo" (Default iOS behavior)
- Lock iPhone
- Say: **"Hey Siri, Open Echo"**
- ✅ Expected: App launches to home screen

#### Test 2: "Start Echo" (Custom shortcut)
- Ensure AirPods/headphones connected
- Say: **"Hey Siri, Start Echo"**
- ✅ Expected:
  - App launches (if not open)
  - Recording starts automatically
  - See recording indicator in app
  - Speak into AirPods mic
  - Verify transcription appears

#### Test 3: "Stop Echo" (Custom shortcut)
- While recording active
- Say: **"Hey Siri, Stop Echo"**
- ✅ Expected:
  - Recording stops
  - Conversation is processed
  - Summary appears

### Step 8: Debugging (If Issues Occur)

**Issue: Shortcuts don't appear in Settings**
```bash
# Solution: Clean build and reinstall
Product → Clean Build Folder (Cmd+Shift+K)
Delete app from iPhone
Rebuild and reinstall
```

**Issue: "Siri doesn't recognize command"**
```bash
# Solution: Re-register shortcuts
Settings → Siri & Search → Echo → Disable → Enable
Try saying command again
```

**Issue: App crashes on Siri invocation**
```bash
# Solution: Check logs
Window → Devices and Simulators
Select iPhone → View Device Logs
Filter: "SiriShortcuts" or "Echo"
```

**Issue: Recording doesn't start**
```bash
# Check:
1. Microphone permission granted?
2. Check Xcode console for Flutter logs:
   "📱 Siri: Start recording (source: siri_shortcut)"
3. Verify CaptureProvider is initialized
```

### Step 9: Verify Logs

**Xcode Console should show:**
```
[SiriShortcuts] IntentHandler: StartEchoIntent invoked
[SiriShortcuts] AppDelegate: Start recording notification received
[SiriShortcuts] AppDelegate: startSession invoked successfully
✅ SiriShortcutsService initialized
📱 Siri: Start recording (source: siri_shortcut)
✅ Siri: Recording started successfully
```

---

## 📋 Final Verification Checklist

- [ ] Intents.intentdefinition created with 2 intents
- [ ] IntentHandler.swift updated to use generated intent classes
- [ ] Siri capability added to project
- [ ] App builds successfully on iPhone
- [ ] "Start Echo" and "Stop Echo" appear in Siri Settings
- [ ] "Hey Siri, Open Echo" launches app
- [ ] "Hey Siri, Start Echo" starts recording
- [ ] "Hey Siri, Stop Echo" stops recording
- [ ] Transcription works via AirPods mic
- [ ] Logs show successful intent handling

---

## Summary

### What We're Adding:
✅ iOS Siri Shortcuts (3 phrases)  
✅ Method channel bridge to existing `CaptureProvider`  
✅ Headset mode indicator (optional UX polish)  
✅ Audio route detection (optional UX polish)

### What We're NOT Adding:
❌ New state machines  
❌ New session managers  
❌ New BLE logic  
❌ Background recording  
❌ Always-on listening  
❌ New audio processing

### Key Principle:
**Connect Siri → Existing Omni Logic → Zero Architecture Changes**

This ensures:
- Fast implementation (~1 week)
- Low risk (no core refactors)
- App Store compliant (explicit user actions only)
- Maintainable (reuses Omni's battle-tested code)
