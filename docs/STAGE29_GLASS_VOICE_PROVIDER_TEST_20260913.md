# Meboard Stage 29 — resource-safe privacy fix + black glass + voice-provider long press

Status: **signed test APK; static/build verification PASS; phone runtime pending; privacy-final NO**.

## Artifact

- `Meboard-stage29-Glass-VoiceProviderChooser-TEST.apk`
- SHA-256: `8da8eb3b7e886c8e5c4d2d7ed467780e2b85d7fdb47590ccf713727ae17d1152`
- Size: `110115756` bytes.
- Package: `com.mekromn.meboard`.
- Version code/name: `175940518` / `18.0.3.954559732-release-arm64-v8a`.
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`.

Stage 27 remains the last user-confirmed working rollback. The original Stage 28 is **failed** and must not be promoted: it rebuilt `resources.arsc` incorrectly, causing unresolved resources including the launcher icon and a startup crash. Stage 28b was an internal resource-safe repair that preserved the Stage-27 resource table. Stage 29 is built on Stage 28b.

## Resource/crash fix boundary

Compared with Stage 28b, Stage 29 changes only `classes.dex` and `AndroidManifest.xml`; the other 9146 payload entries are decompressed-byte-identical. `resources.arsc`, both privacy XML files, all assets and all 16 native libraries are unchanged. The final signed APK resolves `res/mipmap-anydpi-v21/ic_app.xml` normally in `aapt2 dump badging` and produces no missing-resource warning.

The manifest has one semantic change only: an `android.speech.RecognitionService` `<queries>` intent so installed recognition services can be enumerated under Android package-visibility rules. Re-decoding the compiled manifest produces a one-block textual diff containing only that query.

## Black glass theme

A guarded helper is called after the normal IME input view is constructed. It applies a translucent black IME window, `Window.setBackgroundBlurRadius(90)`, `WindowManager.LayoutParams.setBlurBehindRadius(56)` with `FLAG_BLUR_BEHIND`, translucent navigation/decor treatment, and background-only alpha adjustment on the input view. It does not reduce text/key-child alpha.

The helper catches `Throwable`, so theme application failure falls back to the existing keyboard instead of intentionally crashing the IME. Android can disable cross-window blur at runtime; the translucent black treatment remains as the fallback.

## Microphone gesture contract

Normal tap behavior is not patched. Existing access-point click dispatch `mic.m` is byte-identical to Stage 28b, and nine core recognizer/voice classes are byte-identical (`kgm`, `kgw`, `kht`, `kjp`, `kjm`, `kig`, `fct`, `ruo`, `rrf`).

Long press is installed only for the `WIDGET_VOICE_KEY` access-point location; a SoftKeyboardView voice-key fallback is also intercepted by localized voice accessibility labels. Long press opens a popup with **Meboard standard voice typing** plus each visible installed `android.speech.RecognitionService`. Selecting standard explicitly invokes the unchanged normal click path. Selecting another provider creates `SpeechRecognizer` for that explicit `ComponentName`, listens once, and commits the first final result to the current `InputConnection`. Provider choice is not persisted and does not alter future normal taps. Cancelling the popup starts no recognition.

The selected external provider may itself use network/cloud services according to its implementation. Choosing it is an explicit user action; this build does not claim third-party recognizers are offline/private.

## Privacy cleanup retained

The resource-safe Stage-28b cleanup remains intact: `Share usage statistics`, `Improve for everyone`, and `Audio donations` are absent from the privacy screen; the corresponding managed-settings entries are absent; direct `VoiceDonationManager` / `maybeAddDonationRequest` remains absent; `Personalize for you` and `Delete learned words and data` remain.

Privacy work is not complete. Remaining usage-metrics infrastructure, federated remnants, Primes/diagnostic code and native mixed reporting code still require review.

## Verification

- Stage 28b class count 21744 -> Stage 29 21749: exactly five Meboard helper/listener classes added, zero deleted.
- Existing main-DEX classes modified: exactly three (`SoftKeyboardView`, `mic`, `oup`).
- Exactly one method in each changed class differs; the other **223 methods** are byte-identical after a fresh decode of the signed APK.
- All four DEX headers, SHA-1 signatures, Adler32 checksums and file-size headers pass.
- ZIP CRC passes.
- 16-KiB native-library ZIP alignment passes.
- APK Signature Scheme v3 passes with the stable Meboard certificate.
- Final badging resolves package, Meboard label and launcher icon without missing-resource warnings.
- Actual signed output was freshly decoded with Apktool 3.0.3 and the intended source/class delta reproduced exactly.
- No on-device runtime test was performed in the build environment.
