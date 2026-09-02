# Keyboard privacy cleanup

Reproducible reverse-engineering workspace for removing telemetry and unnecessary background networking from the supplied Gboard 18.0.3 arm64 bundle while preserving keyboard functionality.

## Current source bundle

- `Gboard_175940518_18.0.3.954559732-release-arm64-v8a.aspk`
- Base APK plus Brella, Dictation, Tenor animation, and xxhdpi splits.

The proprietary APK itself is **not** committed to this public repository.

## Privacy objective

Remove or hard-disable nonessential telemetry, diagnostics upload, analytics/metrics upload, federated-learning/background training transport, experiment/remote-configuration traffic that is not required for core typing, and other unsolicited background network activity.

Preserve only network features that are genuinely user-facing or explicitly requested, such as optional language/model downloads, voice/dictation when enabled, GIF/sticker lookup when used, and similar intentional features.

## Rule

A hostname blocklist alone does not count as telemetry removal. Components and call paths should be removed or made inert wherever practical, with manifest/service cleanup and verification afterward.

See `docs/TELEMETRY_AUDIT.md` and `tools/audit_bundle.py`.
