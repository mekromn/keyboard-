# Meboard Stage 33 — live preview + live keyboard AMOLED hook + mic long-click enable

Status: signed test APK; static/build checks PASS; phone runtime pending; privacy-final NO.

## Artifact

- APK: `Meboard-stage33-LIVE-PREVIEW-AMOLED-MIC-LONGPRESS-FIX-TEST.apk`
- SHA-256: `4f63365ae817b6a5de7003820e3c62df20ed22ca4fae4eca7dee8ae98e42d168`
- Size: 110115756 bytes
- Package: `com.mekromn.meboard`
- Stable signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`
- Exact Stage-32 input SHA-256: `4c533d06a93724538b4423e61b9b8fea99858eab8cd5be29dfd57e0d913aae29`

## Stage-32 device failures traced

The new Theme radio existed but only changed a pending boolean; it never changed either live preview ImageView. The Apply path also targeted the Theme-details hierarchy instead of the live keyboard tree. Stage 32 therefore had no safe runtime call applying `MeboardGlass` to the real `SoftKeyboardView`.

The mic wrapper was attached to the correct voice-key long-click listener, but stock key metadata left the voice `SoftKeyView` non-long-clickable. Android therefore never invoked the wrapper, and Gboard later restores the stock long-clickable state.

## Stage-33 changes

Exactly five existing classes change, with no class additions/deletions:

- `MeboardThemeMode`: updates Theme preview views `0x7f0b2a51`/`0x7f0b2a52` immediately for the pending selection and restores committed state on Apply/Cancel.
- `MeboardThemeMode$Listener`: radio changes now call both `setPending` and `updatePreview`.
- `SoftKeyboardView`: safely calls `MeboardGlass.applyBody(this)` on attach and when the keyboard becomes visible. There is no whole-window blur and no `oup.onStartInput` surgery.
- `VoiceProviderChooser`: `prepareVoiceKey(View)` forces long-clickability only for the exact voice key.
- `SoftKeyView`: calls `prepareVoiceKey(this)` after the wrapped stock long-click listener is installed and again after stock state restoration.

Short-tap voice handling is not replaced by this patch. If the chooser opens but a selected third-party RecognitionService fails, that is a separate provider-compatibility problem.

The preview is an immediate visual indicator, not claimed as a bitmap-perfect re-render: AMOLED mode gives the preview a black background, alpha 0.88 and translucent black SRC_ATOP filter; Theme background restores normal preview rendering.

## Signed-output verification

Fresh decode of the actual signed output versus Stage 32:

- classes: 21751 -> 21751
- classes added/deleted: 0 / 0
- modified classes: exactly the five above
- unchanged classes: 21746
- non-signature payload entries: 9148 -> 9148
- changed payload: `classes.dex` only
- unchanged payload entries: 9147
- `AndroidManifest.xml`, `resources.arsc`, `classes2.dex`, `classes3.dex`, `classes4.dex`: byte-identical
- all 16 native libraries: byte-identical
- DEX header SHA-1/Adler32/file-size checks: PASS
- ZIP integrity and 16-KiB native alignment: PASS
- APK Signature Scheme v3 with permanent Meboard certificate: PASS

Final `classes.dex` SHA-256: `fbb7e43555c0330f8779ab353256e9981566252dc131c2dd5e8d3b069e3c4a87`.

## Runtime gate

Do not promote until the phone confirms:

1. AMOLED selection changes the Theme preview immediately.
2. Apply + open keyboard makes the live keyboard body AMOLED black/glass.
3. Theme background + Apply restores the original theme background.
4. Short mic tap remains stock dictation.
5. Long-pressing the same toolbar mic opens the provider chooser.

This stage does not advance the remaining telemetry/native/network cleanup and makes no privacy-final claim.
