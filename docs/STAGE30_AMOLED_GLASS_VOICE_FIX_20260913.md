# Meboard Stage 30 — optional AMOLED black glass + microphone long-press fix

Status: signed test APK; static/build verification PASS; phone runtime pending; privacy-final NO.

Artifact: `Meboard-stage30-AMOLED-Glass-VoiceProvider-FIX-TEST.apk`

- SHA-256: `d4b02b814538a051f3c81caf429aa8c981d71c1aab169fb3c14221788b45e27d`
- Size: 110115756 bytes
- Package: `com.mekromn.meboard`
- Version code/name: 175940518 / 18.0.3.954559732-release-arm64-v8a
- Stable signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

Stage 27 remains the last broadly user-confirmed rollback. Stage 29 launched but its whole-window blur was visually wrong and its microphone long-press did not trigger, so Stage 29 is not a working checkpoint.

## AMOLED black glass preference

A persistent independent switch was added at the bottom of the existing Preferences screen:

`AMOLED black glass keyboard background`

Preference key: `meboard_amoled_black_glass`. Default: false.

It is an independent switch rather than a mutually-exclusive radio-theme choice because the requested behavior is to combine it with any selected keyboard theme. When off, the helper exits without changing the keyboard background. When enabled, it applies a true-black high-opacity glass background only to the keyboard input-view layer and makes the navigation bar black. It explicitly clears the Stage-29 whole-window blur/blur-behind flags and never enables them. Selected themes continue to own keys, labels, accents and suggestion styling.

The preference XML is the only resource payload changed. `resources.arsc` remains byte-identical to Stage 29, avoiding the Stage-28 resource-table failure. Fresh decode has zero missing-resource warnings and the launcher resolves to `res/mipmap-anydpi-v21/ic_app.xml`.

## Microphone long-press fix

Stage 29 relied on Android `OnLongClickListener` / a higher-level soft-key callback that did not trigger on the actual microphone access-point view on device.

Stage 30 keeps the `WIDGET_VOICE_KEY` bind point but installs a touch-timer detector directly on that view. It uses Android's normal `ViewConfiguration.getLongPressTimeout()`, leaves short taps unconsumed, cancels on release/cancel, consumes only the release after a successful long-press, and gives long-press haptic feedback before showing the provider chooser.

The Stage-29 `SoftKeyboardView.onLongClick()` fallback hook is removed. The method is byte-identical to Stage 27 again. The normal mic dispatcher `mic.m(Lmif;Landroid/view/View;)V` is byte-identical across Stage 27, Stage 29 and Stage 30, so normal tap retains the original Meboard voice path.

The provider chooser still enumerates visible `android.speech.RecognitionService` implementations, includes `Meboard standard voice typing`, and does not persist external-provider selection.

## Privacy cleanup retained

The Stage-28/29 privacy cleanup remains present. Inspected smali/settings XML contains no `enable_user_metrics`, `user_enable_federated_training`, `enable_voice_donation`, `VoiceDonationManager` descriptor `Lrqw;`, or `maybeAddDonationRequest`. This is not a claim of whole-app privacy completion.

## Verification

Compared with Stage 29, exactly two decompressed APK payloads changed: `classes.dex` and `res/xml/setting_preferences.xml`. The other 9146 of 9148 payload entries are byte-identical, including `resources.arsc`, `AndroidManifest.xml`, DEX files 2–4, all assets, and all 16 native libraries.

Main-DEX class count is 7464 -> 7465. `VoiceProviderChooser$LongPressListener` was removed; `VoiceProviderChooser$TouchListener` and `VoiceProviderChooser$ShowRunnable` were added. Total APK class count is 21749 -> 21750.

Nine watched voice/recognizer classes (`kgm`, `kgw`, `kht`, `kjp`, `kjm`, `kig`, `fct`, `ruo`, `rrf`) are byte-identical to Stage 27. ZIP CRC, 16-KiB native alignment, APK Signature Scheme v3, stable certificate, launcher resource resolution, and a fresh full decode all pass.

No Android runtime test was performed in the build environment. Device acceptance still needs startup/icon, normal typing, preference toggle with several themes, normal mic tap, and microphone long-press/provider selection.
