# Meboard Stage 39 — Stage-35 long-press path with live AccessPointsManager anchor

Status: signed runtime test. Mic-only isolation build; no theme work.

## Why Stage 39 returns to Stage 35
On-device results established a useful progression:
- Stage 35: short press worked normally; long press produced no built-in dictation and no chooser.
- Stages 36/37/38a: short press worked, but long press collapsed back into the same built-in dictation behavior.

That makes Stage 35 the strongest evidence that Gboard was actually selecting a separate LONG_PRESS ActionDef. Stage 39 therefore starts from the exact signed Stage-35 APK and changes only the part after that long-press action has already been selected.

## Root cause targeted
Stage 35's LONG_PRESS ActionDef uses Gboard's built-in `ACCESS_POINT_ACTION` (`-0x9c47`) with `VoiceProviderActionRunnable`. Fresh inspection confirms `AccessPointsManager.consumeEvent()` executes Runnable payloads for that action.

The Stage-35 Runnable then calls `VoiceProviderChooser.showCurrentChooser()`, which depends on a separately populated WeakReference to the mic view. If the active toolbar path never populates or retains that WeakReference, the Runnable is consumed but silently returns false. That exactly matches the observed Stage-35 runtime behavior: hold is different from tap, but no UI appears.

## Stage 39 change
Only `mln` (`AccessPointsManager`) is changed relative to Stage 35.

When action `-0x9c47` contains **our exact** `VoiceProviderActionRunnable`:
1. retain the live `AccessPointsManager` instance;
2. read its current attached keyboard view from `mln.j[Lppe.a.ordinal()]`;
3. search that live attached root for the toolbar mic id `0x7f0b2b26`;
4. use the mic if found, otherwise use the attached keyboard root itself;
5. perform haptic feedback;
6. call `VoiceProviderChooser.showChooser(anchor)` directly.

If no live anchor is available or `showChooser()` returns false, the original Runnable execution path remains as fallback.

All other ACCESS_POINT_ACTION Runnables retain their original behavior.

## Exact artifact
- APK: `Meboard-stage39-STAGE35-LIVE-ANCHOR-CHOOSER-TEST.apk`
- SHA-256: `5141792d143127e53f32f81cfe628c55fd6eb335b7f6691afed317d21dc66d48`
- Size: 110,111,660 bytes
- Package: `com.mekromn.meboard`
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`
- APK Signature Scheme: v3 only
- 16 KiB native-library alignment: PASS

## Stage 35 → Stage 39 package delta
Decompressed payload comparison of all 9,148 ZIP entries:
- exactly one payload changed: `classes.dex`;
- `classes2.dex`, `classes3.dex`, `classes4.dex`, manifest, resources, assets, and all native libraries are byte-identical.

Fresh decode comparison:
- exactly one existing smali class changed: `smali/mln.smali`;
- no classes added or removed relative to Stage 35.

The Stage-35 mic model, short-press behavior, provider chooser implementation, RecognitionService package-visibility query, and helper classes are otherwise unchanged.

## Required device gate
1. Show the keyboard; it must not crash.
2. Short-tap microphone: ordinary Meboard built-in voice typing.
3. Long-press microphone: provider chooser should appear instead of built-in voice typing.
4. Cancel chooser: nothing starts.
5. Choose alternate provider: one-shot recognition should commit text.
6. Next short tap: ordinary built-in voice typing again.

If long press again produces nothing, the remaining failure is UI presentation/anchor rather than gesture separation. If built-in dictation starts on hold, then Stage-35 separation was not actually preserved on this active configuration and the premise must be revised.
