// This is a SAFE placeholder to keep the repo buildable without committing
// real Firebase project config.
//
// To generate real options locally:
//   flutterfire configure
//
// Then replace this file (DO NOT COMMIT production credentials).

import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;

class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    // NOTE: Placeholder values. Firebase initialization will fail until replaced.
    return const FirebaseOptions(
      apiKey: 'REPLACE_ME',
      appId: 'REPLACE_ME',
      messagingSenderId: 'REPLACE_ME',
      projectId: 'REPLACE_ME',
    );
  }
}
