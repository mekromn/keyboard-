# Meboard

Reproducible reverse-engineering workspace for building **Meboard**, a coexistence-safe privacy-focused keyboard derived from the supplied Gboard 18.0.3 arm64 bundle while physically removing telemetry and unnecessary background networking.

## Identity

- App name: `Meboard`
- Coexistence package/application ID: `com.mekromn.meboard`
- Stock/system Gboard remains untouched and can stay installed/enabled.
- Meboard uses its own signing identity and must not attempt to update or replace `com.google.android.inputmethod.latin`.

The implementation must update package-bound manifest authorities, custom permissions, deep links, split metadata, package literals that identify the running app, and other self-references required for clean coexistence. Java/smali class namespaces do not need cosmetic renaming when they are implementation class names rather than application identity.

## Current source bundle

- `Gboard_175940518_18.0.3.954559732-release-arm64-v8a.aspk`
- Base APK plus Brella, Dictation, Tenor animation, and xxhdpi splits.

The proprietary APK itself is **not** committed to this public repository.

## Privacy objective

Physically excise all telemetry/analytics/diagnostics-upload/federated-training/remote-experiment code and all unnecessary network logic from the application binary. Preserve only networking that is required for deliberately retained, user-triggered features.

## Non-negotiable removal rule

**Disabled is not removed.** The following do **not** count as completion:

- Feature flags set to false.
- No-op telemetry methods or stub classes.
- Early-return patches that leave telemetry implementations in DEX/native code.
- Hostname/domain blocklists.
- Firewall-only mitigation.
- Manifest-only disabling while implementation code remains.
- Leaving unreachable/dead telemetry classes in the APK.
- Renaming telemetry symbols while retaining their logic.

Telemetry code must be physically absent from rebuilt DEX/resources/native libraries wherever technically separable. Dedicated telemetry packages/classes/components are deleted. When telemetry is mixed into a shared class, its telemetry methods, fields, branches, registrations, scheduling, serialization, persistence, and transport logic are surgically removed, followed by dead dependency cleanup.

## Network rule

Network code is retained only for features explicitly chosen to remain, such as optional model/language downloads, active dictation, or user-invoked GIF/sticker search. Background network paths with no required user-facing purpose are removed, not merely blocked.

## Acceptance

A build is not accepted until static verification confirms the targeted telemetry implementation and registrations are absent, the package is `com.mekromn.meboard`, the visible keyboard name is Meboard, it installs alongside system Gboard, and runtime testing shows no unsolicited network activity during idle use or ordinary offline typing.

See:

- `docs/TELEMETRY_AUDIT.md`
- `docs/PHYSICAL_REMOVAL_POLICY.md`
- `tools/audit_bundle.py`
- `tools/verify_physical_removal.py`
