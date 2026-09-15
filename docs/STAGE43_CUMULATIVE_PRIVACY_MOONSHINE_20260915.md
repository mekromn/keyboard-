# Meboard Stage 43 — cumulative privacy + Moonshine

Status: signed cumulative test candidate. Runtime confirmation pending.

## Purpose

Stage 43 fixes the branch-lineage regression that allowed previously removed privacy UI and donation code to reappear in the later microphone builds.

The base is the Stage-42 Moonshine build, preserving its confirmed microphone behavior. Only the resource-safe Stage-28 privacy payloads are transplanted from the Stage-29 binary donor.

## Exact artifact

- APK: `Meboard-stage43-CUMULATIVE-PRIVACY-MOONSHINE-TEST.apk`
- SHA-256: `378804d81aba41fd6daf6a37e94d88c6e6fedecb700b66f5ca2ecb036059a0d8`
- Size: 110012835 bytes
- Package: `com.mekromn.meboard`
- Version code: `175940518`
- Version name: `18.0.3.954559732-release-arm64-v8a`
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

## Cumulative merge boundary

Stage 43 starts from the exact Stage-42 APK and replaces exactly three decompressed APK payloads with the corresponding resource-safe privacy-cleaned payloads from Stage 29:

1. `classes2.dex`
2. `res/xml/setting_privacy.xml`
3. `res/xml/APKTOOL_RENAMED_0x7f170002.xml`

No Stage-29 main DEX, theme code, microphone code, manifest, resource table, assets, native libraries, or other payloads are imported.

Compared with Stage 42:

- `classes.dex`: byte-identical
- `AndroidManifest.xml`: byte-identical
- `resources.arsc`: byte-identical
- `classes3.dex`: byte-identical
- `classes4.dex`: byte-identical
- all native libraries: preserved from Stage 42

The Stage-29 donor and Stage 42 use the same resource table, so the compiled Stage-28 privacy XML payloads can be transplanted without rebuilding `resources.arsc`.

## Locked removals restored

The cumulative candidate restores the verified Stage-28 removals:

- Privacy row `Share usage statistics`: absent
- Privacy row `Improve for everyone`: absent
- Privacy row `Audio donations`: absent
- managed restriction `enable_user_metrics`: absent
- managed restriction `user_enable_federated_training`: absent
- `rqw` / `VoiceDonationManager`: physically absent
- `Lrqw;` references: absent
- `maybeAddDonationRequest`: absent
- `PrivacySettingsFragment.aD(boolean)`: absent

Retained local controls remain:

- `Personalize for you`
- `Delete learned words and data`

## Stage-42 Moonshine behavior preserved

The main DEX is byte-identical to Stage 42. The verified helper path still contains:

- preferred provider package `org.futo.voiceinput.moonshine`
- direct Moonshine launch on microphone long press
- normal Meboard dictation on short microphone tap
- deferred `InputConnection.commitText()` result insertion
- bounded delayed retry while the original editor regains focus
- Android provider chooser fallback when Moonshine cannot resolve

No Stage-29 glass/theme implementation was imported.

## Verification

- APK Signature Scheme v3: PASS
- permanent Meboard signer preserved
- ZIP/native 16-KiB alignment: PASS
- package badging resolves label `Meboard`
- payload names preserved
- exact Stage-42-to-Stage-43 changed payload set: the three cumulative privacy payloads listed above
- each transplanted payload is byte-identical to its Stage-29 donor counterpart
- locked-removal verifier: PASS
- decoded DEX/privacy XML checks: PASS

The full resource decode exceeded the execution-call timeout while processing the large resource set; the relevant DEX trees and target XMLs were decoded and independently verified, and the binary payload comparison proves all non-target resource payloads are Stage-42-identical.

## Runtime acceptance gate

Before further cleanup stages, verify on device:

1. Keyboard opens and types normally.
2. Privacy settings contain `Personalize for you` and `Delete learned words and data` but not `Share usage statistics`, `Improve for everyone`, or `Audio donations`.
3. Short microphone tap launches normal Meboard dictation.
4. Long microphone press launches Moonshine directly.
5. Moonshine recognition result is inserted into the original editor.

After this passes, Stage 43 becomes the cumulative base. Future candidates must descend from Stage 43 or a verified descendant and must pass the locked-removal regression gate before delivery.
