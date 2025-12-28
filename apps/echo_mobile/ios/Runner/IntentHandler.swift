//
//  IntentHandler.swift
//  Echo
//
//  Handles iOS Siri Shortcuts (Intents) for AirPods-first activation.
//  Maps "Start Echo" and "Stop Echo" Siri commands to Flutter MethodChannel calls.
//
//  Architecture: Minimal bridge - posts NotificationCenter events that AppDelegate
//  forwards to Flutter via MethodChannel. No new state management.
//
//  NOTE: This file requires Intents.intentdefinition to be created in Xcode.
//  See docs/SIRI_SHORTCUTS_INTEGRATION.md for macOS completion steps.
//

import Intents
import UIKit

@available(iOS 12.0, *)
class IntentHandler: INExtension {
    
    // MARK: - Lifecycle
    
    override func handler(for intent: INIntent) -> Any {
        // Route intents to appropriate handlers
        // Note: Xcode will generate StartEchoIntent and StopEchoIntent
        // from Intents.intentdefinition file
        
        if intent is INStartWorkoutIntent {
            // StartEchoIntent will be created in Intents.intentdefinition
            // For now, use placeholder - update after creating intentdefinition
            return StartEchoIntentHandler()
        } else if intent is INPauseWorkoutIntent {
            // StopEchoIntent will be created in Intents.intentdefinition
            // For now, use placeholder - update after creating intentdefinition
            return StopEchoIntentHandler()
        }
        
        return self
    }
}

// MARK: - Start Echo Intent Handler

@available(iOS 12.0, *)
class StartEchoIntentHandler: NSObject {
    
    /// Handle "Start Echo" Siri command
    /// Posts notification that AppDelegate bridges to Flutter
    func handle(completion: @escaping (INIntentResolutionResult) -> Void) {
        NSLog("[SiriShortcuts] StartEchoIntent invoked")
        
        // Post notification to AppDelegate
        NotificationCenter.default.post(
            name: NSNotification.Name("EchoStartRecording"),
            object: nil,
            userInfo: ["source": "siri_shortcut", "action": "start"]
        )
        
        // Return success
        // Note: Replace INIntentResolutionResult with proper response type
        // after creating Intents.intentdefinition
        NSLog("[SiriShortcuts] StartEchoIntent completed successfully")
        completion(INIntentResolutionResult())
    }
}

// MARK: - Stop Echo Intent Handler

@available(iOS 12.0, *)
class StopEchoIntentHandler: NSObject {
    
    /// Handle "Stop Echo" Siri command
    /// Posts notification that AppDelegate bridges to Flutter
    func handle(completion: @escaping (INIntentResolutionResult) -> Void) {
        NSLog("[SiriShortcuts] StopEchoIntent invoked")
        
        // Post notification to AppDelegate
        NotificationCenter.default.post(
            name: NSNotification.Name("EchoStopRecording"),
            object: nil,
            userInfo: ["source": "siri_shortcut", "action": "stop"]
        )
        
        // Return success
        NSLog("[SiriShortcuts] StopEchoIntent completed successfully")
        completion(INIntentResolutionResult())
    }
}

// MARK: - macOS Completion Notes
//
// This file is a PARTIAL implementation. To complete:
//
// 1. Open Xcode project workspace
// 2. Create Intents.intentdefinition file with:
//    - StartEchoIntent (custom intent)
//    - StopEchoIntent (custom intent)
// 3. Replace INStartWorkoutIntent/INPauseWorkoutIntent with actual intent types
// 4. Update completion handlers to use proper response types
// 5. Add Siri capability to project
// 6. Build and test on physical iPhone
//
// See docs/SIRI_SHORTCUTS_INTEGRATION.md for detailed steps.
