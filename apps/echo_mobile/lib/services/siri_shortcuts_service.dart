import 'package:flutter/services.dart';
import 'package:echo_mobile/providers/capture_provider.dart';
import 'package:echo_mobile/utils/enums.dart';
import 'package:echo_mobile/utils/logger.dart';

/// Service to handle iOS Siri Shortcuts integration.
///
/// This service bridges iOS Siri Intents (StartEchoIntent, StopEchoIntent)
/// to the existing Omni CaptureProvider methods, enabling hands-free
/// AirPods-first activation via "Hey Siri, Start Echo" / "Stop Echo".
///
/// Architecture: Zero new state machines - reuses existing CaptureProvider.
/// - startSession -> CaptureProvider.streamRecording()
/// - stopSession -> CaptureProvider.stopStreamRecording()
class SiriShortcutsService {
  static const MethodChannel _channel = MethodChannel('com.echo/siri');

  final CaptureProvider _captureProvider;
  bool _isInitialized = false;

  SiriShortcutsService(this._captureProvider);

  /// Initialize the service and set up method call handler.
  /// Should be called early in app lifecycle (main.dart).
  Future<void> initialize() async {
    if (_isInitialized) {
      Logger.debug('SiriShortcutsService already initialized');
      return;
    }

    _channel.setMethodCallHandler(_handleMethodCall);
    _isInitialized = true;
    Logger.info('✅ SiriShortcutsService initialized');
  }

  /// Handle method calls from iOS via MethodChannel.
  Future<void> _handleMethodCall(MethodCall call) async {
    try {
      Logger.info('Siri Shortcut invoked: ${call.method}');

      switch (call.method) {
        case 'startSession':
          await _handleStartSession(call.arguments);
          break;
        case 'stopSession':
          await _handleStopSession();
          break;
        default:
          Logger.warning('⚠️ Unknown Siri Shortcut method: ${call.method}');
      }
    } catch (e, stackTrace) {
      Logger.handle(e, stackTrace, message: '❌ Siri Shortcut error');
    }
  }

  /// Handle "Start Echo" Siri command.
  /// Maps to existing CaptureProvider.streamRecording() method.
  Future<void> _handleStartSession(dynamic arguments) async {
    final source = arguments is Map ? arguments['source'] : 'siri_shortcut';

    Logger.info('📱 Siri: Start recording (source: $source)');

    // Defensive check: Don't start if already recording
    if (_captureProvider.recordingState != RecordingState.stop) {
      Logger.warning(
          '⚠️ Siri: Ignoring start command - already recording (state: ${_captureProvider.recordingState})');
      return;
    }

    try {
      // Use existing CaptureProvider method - NO NEW LOGIC
      await _captureProvider.streamRecording();
      Logger.info('✅ Siri: Recording started successfully');
    } catch (e, stackTrace) {
      Logger.handle(e, stackTrace, message: '❌ Siri: Failed to start recording');
    }
  }

  /// Handle "Stop Echo" Siri command.
  /// Maps to existing CaptureProvider.stopStreamRecording() method.
  Future<void> _handleStopSession() async {
    Logger.info('📱 Siri: Stop recording');

    // Defensive check: Don't stop if not recording
    if (_captureProvider.recordingState == RecordingState.stop) {
      Logger.warning('⚠️ Siri: Ignoring stop command - not recording');
      return;
    }

    try {
      // Use existing CaptureProvider method - NO NEW LOGIC
      await _captureProvider.stopStreamRecording();
      Logger.info('✅ Siri: Recording stopped successfully');
    } catch (e, stackTrace) {
      Logger.handle(e, stackTrace, message: '❌ Siri: Failed to stop recording');
    }
  }

  /// Dispose the service and clean up resources.
  void dispose() {
    _isInitialized = false;
    Logger.debug('SiriShortcutsService disposed');
  }
}
