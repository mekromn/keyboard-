# Meboard Stage 38 — raw microphone DOWN/UP gate

Status: signed runtime test. Mic-only work; no theme changes.

## Runtime evidence driving this build
- Stage 35: holding the toolbar microphone produced no chooser and no useful alternate-provider action.
- Stage 36: holding the microphone launched built-in voice typing exactly like a short tap; short tap remained normal.
- Stage 37: intercepting the access-point LONG_PRESS wrapper still launched built-in voice typing; the chooser never appeared.

Those results establish that downstream ActionDef/payload/AccessPointsManager metadata is not a reliable discriminator for the active toolbar path on-device.

## Stage 38 strategy
Stage 38 moves the split to the earliest proven raw input owner: `SoftKeyboardView.dispatchTouchEvent(MotionEvent)`.

For a DOWN physically inside the actual toolbar voice `SoftKeyView` (`0x7f0b2b26`), Stage 38 consumes the mic gesture before stock Gboard sees it and owns that pointer until UP/CANCEL:

- DOWN: locate the real visible mic by screen bounds, set pressed state, and schedule Android's `ViewConfiguration.getLongPressTimeout()` timer.
- Early UP: cancel the timer, clear pressed state, and call the mic view's existing `performClick()`. `SoftKeyView.n(...)` installs `SoftKeyboardView` as the stock click listener, so this re-enters the original click path rather than launching voice directly from Meboard code.
- Hold timeout: call the existing `VoiceProviderChooser.handleLongPress()` and mark the gesture consumed only if the chooser actually opens.
- UP after a successful hold: no `performClick()` is issued, so stock built-in voice typing cannot start behind the chooser.
- CANCEL: cancel timer and clear state without launching anything.
- Every non-mic MotionEvent returns immediately to the original `SoftKeyboardView.dispatchTouchEvent()` implementation.

This intentionally does not depend on `View.OnLongClickListener`, `pvi`, ActionDef payload survival, or AccessPointsManager gesture metadata.

## Exact signed artifact
- APK: `Meboard-stage38-RAW-MIC-DOWN-UP-GATE-TEST.apk`
- SHA-256: `5093258e545fb3c0aedb5bdb1a39d89804b568e0d48e161a5e2a29f16eeb1c88`
- Size: 110,021,051 bytes
- Package: `com.mekromn.meboard`
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`
- Signature: APK Signature Scheme v3 only
- 16 KiB native-library alignment: PASS

## Stage 37 → Stage 38 packaged delta
After decompression and ignoring signature records:
- exactly one payload changed: `classes.dex`;
- `classes2.dex`, `classes3.dex`, `classes4.dex`, `AndroidManifest.xml`, `resources.arsc`, assets, and all native libraries are byte-identical.

Fresh decode of the final signed APK versus the final signed Stage 37 decode changes exactly four smali classes:
- existing `com/google/android/libraries/inputmethod/widgets/SoftKeyboardView`;
- added `com/mekromn/meboard/VoiceMicTouchGate`;
- added `VoiceMicTouchGate$State`;
- added `VoiceMicTouchGate$HoldRunnable`.

No existing voice/recognizer implementation class is edited in this stage.

## Required device gate
1. Short tap microphone: ordinary Meboard voice typing must start normally.
2. Hold microphone past the normal Android long-press delay: provider chooser must appear.
3. Built-in voice typing must NOT start underneath/after the chooser.
4. Cancel chooser: nothing starts.
5. Choose an alternate provider: one recognition session should commit text.
6. Next short tap: ordinary Meboard voice typing again.
