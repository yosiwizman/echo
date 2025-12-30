# Echo Mobile (Flutter)

This is the primary Flutter application for Echo.

## Quickstart

See the repo root `README.md` for end-to-end instructions.

From this directory:

```bash
flutter pub get
flutter test
flutter analyze --no-fatal-infos --no-fatal-warnings
```

## Local configuration (no secrets committed)

- App env values are read via `envied`:
  - Template: `.env.template`
  - Expected local files:
    - `.dev.env` (dev)
    - `.env` (prod)

The repo includes **safe placeholder** generated files so `flutter analyze` works
without local secrets:
- `lib/env/dev_env.g.dart`
- `lib/env/prod_env.g.dart`

To generate real values locally (do not commit):

```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

## Firebase

This repo includes placeholder `lib/firebase_options_dev.dart` and
`lib/firebase_options_prod.dart` so the app compiles.

Generate real Firebase options locally with the FlutterFire CLI and replace the
placeholders (do not commit production config).
