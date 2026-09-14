# Meboard Stage 37 — mic wrapper LONG_PRESS interception test

Status: **signed test APK; static/build verification PASS; phone runtime pending**.

## Why Stage 37 exists

Runtime feedback established a useful progression:

- Stage 35: short mic tap worked, but long press did nothing.
- Stage 36: short mic tap still worked, and long press now fired, but it launched built-in Meboard voice typing exactly like a short tap.

That proves Stage 36 reached the real voice-action route but lost the press-vs-hold distinction before the late voice-handler interception.

The Stage-27/36 access-point audit found the surviving discriminator one layer earlier. The toolbar access-point wrapper stores the original gesture enum (`PRESS`, `LONG_PRESS`, etc.) in `mgw.d`. `AccessPointsManager.consumeEvent` (`mln.m`) still has that enum while it resolves the original `ActionDef`; after that, the manager can unwrap/re-emit the action and the distinction can collapse into an ordinary voice launch.

## Stage 37 change

Stage 37 preserves Stage 36's mic ActionDefs and provider chooser implementation. It changes only `mln.m(Lnur;)Z`:

1. After resolving the original wrapped `ActionDef`, compare the access-point gesture enum with `pmy.b` (`LONG_PRESS`).
2. If and only if it is `LONG_PRESS`, inspect the original action.
3. If that original action is `-0x273a` (`LAUNCH_VOICE_IME`), invoke `VoiceProviderChooser.showCurrentChooser()`.
4. If the chooser opens successfully, consume the wrapper event before Gboard re-emits it as ordinary voice typing.
5. If any condition fails, fall straight through to the original Stage-36 behavior.

A normal mic `PRESS` never enters the new branch, so the stock short-tap path remains unchanged.

## Artifact

- Input: `Meboard-stage36-MIC-STOCK-PAYLOAD-HANDLER-TEST.apk`
- Output: `Meboard-stage37-MIC-WRAPPER-LONGPRESS-CHOOSER-TEST.apk`
- Output SHA-256: `c60ce3f86d7c94cb4e48c83d481f120530edca0cbd234f41e4fe67ac324512ee`
- Output size: `110021051` bytes
- Package: `com.mekromn.meboard`
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

## Final signed-output verification

Stage 36 → Stage 37 non-signature payload comparison:

- payload entries in each APK: **9,143**
- changed payload entries: **`classes.dex` only**
- added payload entries: **none**
- deleted payload entries: **none**
- `classes2.dex`: byte-identical
- `classes3.dex`: byte-identical
- `classes4.dex`: byte-identical
- `resources.arsc`: byte-identical
- `AndroidManifest.xml`: byte-identical
- assets and all native libraries: unchanged as part of the one-payload delta

DEX hashes:

- Stage 36 `classes.dex`: `ce6f580e7ec3eca4c2d5cf964978057a37c85b353bc832f9c2e0501660cbbd8e`
- Stage 37 `classes.dex`: `84c70f515f13f924ab9f1403ecf45621967047ba212d6641e8d5dd8d4e54ec4c`

Fresh decode comparison found no added or deleted classes. Aside from Apktool bookkeeping, the **only decoded implementation file changed is `smali/mln.smali`**.

Packaging checks:

- APK Signature Scheme v3: **PASS**
- v1/v2: not used, matching the existing Meboard signing profile
- stable Meboard signer certificate: **PASS**
- ZIP integrity: **PASS**
- 16 KiB native-library alignment (`zipalign -P 16`): **PASS**

## Runtime acceptance test

Test the microphone before anything else:

1. Short tap mic → normal Meboard built-in dictation.
2. Long press the same mic → provider chooser should appear.
3. Release after chooser appears → built-in dictation must **not** start behind it.
4. Cancel chooser → no recognition session starts.
5. Choose an alternate installed provider → one-shot recognition session.
6. Next short tap → normal Meboard built-in dictation again.
7. Next long press → chooser again.

This remains a test build until phone runtime confirms the wrapper interception. No theme work is included in this stage.
