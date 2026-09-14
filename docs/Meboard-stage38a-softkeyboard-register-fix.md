# Meboard Stage 38a — SoftKeyboardView register verifier repair

Status: signed runtime test. Surgical repair of the Stage 38 keyboard-show crash; raw mic-gate behavior is otherwise unchanged.

## Device evidence
Stage 38 crashed as soon as the keyboard was shown.

## Root cause
Stage 38 inserted `VoiceMicTouchGate.onDispatch(...)` at the beginning of `SoftKeyboardView.dispatchTouchEvent(MotionEvent)` and stored its boolean return value in `v0`. Stock code had already loaded the String `"SoftKeyboardView Dispatch Event: "` into `v0` and shortly afterward passed `v0` to `StringBuilder.<init>(String)`. The Stage 38 insertion therefore changed the verifier type of `v0` from `java.lang.String` to integer/boolean before the stock constructor use. Smali assembled, but Android ART can reject the method/class when the keyboard loads.

## Fix
Stage 38a stores the gate result in `v2` instead. `v2` is a safe scratch register at the insertion point and stock code overwrites it with the MotionEvent action immediately afterward. `v0` remains the original String until its stock use.

No raw mic-gate timing, hit testing, chooser behavior, short-tap behavior, resources, manifest, or native code is changed.

## Artifact
- `Meboard-stage38a-STARTUP-REGISTER-FIX-RAW-MIC-GATE-TEST.apk`
- SHA-256 `68101a2ea852412831866b54924c8fb4a3fde22f2a52e1ffdce0d27360e9dd02`
- 110,021,051 bytes
- package `com.mekromn.meboard`
- signer certificate SHA-256 `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`
- APK Signature Scheme v3: PASS
- 16 KiB native-library alignment: PASS

## Stage 38 → Stage 38a delta
Ignoring META-INF signature records, exactly one packaged payload differs: `classes.dex`. The payload entry count remains 9,143. `classes2.dex`, `classes3.dex`, `classes4.dex`, AndroidManifest.xml, resources.arsc, assets and native libraries are byte-identical. Final APK size is exactly the same as Stage 38.

A fresh decode of the actual signed Stage 38a APK confirms the gate result uses `v2` and stock `v0` remains the String.

## Runtime gate
First verify the keyboard can be shown without crashing. If it loads normally: quick mic tap should start stock dictation; holding the mic past the long-press timeout should open the provider chooser; releasing after the chooser should not start built-in dictation.
