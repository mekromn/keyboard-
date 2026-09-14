# Meboard Stage 36 — stock voice-payload handler provider chooser

Status: signed mic-only test candidate; static/build verification passed; device runtime test pending.

Device feedback driving this stage: Stage 35 launched but long-press still did not display the provider chooser. This excludes Stage 35 as a working mic implementation.

Confirmed-good rollback: Stage 27 (`1827fc3a917f28d466f6572e3967acd669f5836df1e8cb2d432adb58c3d66841`).

Stage 36 APK SHA-256: `625776c182bb392953ecab39168c80ffc553976bb824e30b3f3ce3c2fc2e9781`.

## Root cause corrected

Stage 35 replaced the voice access-point LONG_PRESS action code with Gboard's generic Runnable access-point action (`-0x9c47`). The actual voice handler `iew.f()` proves that the stock microphone path is dispatched as `LAUNCH_VOICE_IME` (`-0x273a`), and the stock mic hold is distinguished by payload `talkback_sticky_or_language_picker`.

Stage 36 stops substituting a foreign action type. It keeps the long press in the same action family as the working short tap:

- PRESS: `-0x273a`, payload null — stock, unchanged.
- LONG_PRESS: `-0x273a`, payload `talkback_sticky_or_language_picker` — stock voice action/payload, forced present for the mic.
- DOUBLE_TAP: `-0x273a`, payload `sticky` — stock conditional behavior preserved.

Inside the real `iew.f()` voice handler, after the real voice action has arrived, Stage 36 tests only for `talkback_sticky_or_language_picker`. It calls `VoiceProviderChooser.showCurrentChooser()`. If the chooser reports success, the event is consumed. If the chooser cannot open, execution falls through to Gboard's original handling.

## Signed-output verification

Fresh decode versus Stage 35:

- changed existing classes: exactly `unb` and `iew`;
- removed now-unused custom class: `VoiceProviderActionRunnable`;
- unchanged provider helpers: `VoiceProviderChooser`, `VoiceProviderChooser$MenuListener`, `VoiceProviderChooser$ResultListener`;
- `mhe` voice-view WeakReference marker unchanged from Stage 35;
- no theme code added.

At APK payload level versus Stage 35, only `classes.dex` changed. `AndroidManifest.xml`, DEX 2–4, `resources.arsc`, assets, and all 16 native libraries are byte-identical.

Versus Stage 27, the changed existing main-DEX classes are `iew`, `mhe`, and `unb`, with exactly three `VoiceProviderChooser*` classes added and no Stage-27 class removed. The manifest only adds package visibility for `android.speech.RecognitionService`.

Packaging checks: APK Signature Scheme v3 PASS; stable signer certificate SHA-256 `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`; ZIP integrity PASS; 16-KiB native-library alignment PASS; fresh Apktool 3.0.3 DEX decode PASS.

## Runtime acceptance

1. Short tap mic -> ordinary Meboard dictation.
2. Long-press the same mic -> provider chooser.
3. Release after chooser appears -> ordinary dictation must not start behind it.
4. Cancel -> no recognition session.
5. Select an alternate RecognitionService -> one-shot recognition and text insertion.
6. Next short tap -> ordinary Meboard dictation again.
7. Next long press -> chooser again; no provider is persisted.

If step 2 still fails, the next diagnostic is no longer generic gesture routing: instrument `iew.f()` directly because it is on the proven `LAUNCH_VOICE_IME` consumer path.
