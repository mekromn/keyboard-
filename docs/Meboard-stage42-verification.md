# Meboard Stage 42 — Moonshine default voice input target

Status: signed test APK; static/build verification PASS; phone runtime pending.

## Goal
Preserve the user-confirmed working Stage 41 microphone behavior while changing only the direct long-press external voice target from standard FUTO Voice Input to the Moonshine standalone fork.

- Short mic tap remains the existing Meboard/Gboard voice path.
- Long mic press keeps Stage 41's proven distinct long-press route.
- Preferred external provider package is now `org.futo.voiceinput.moonshine`.
- The Stage 41 fallback Android voice-provider chooser is unchanged if Moonshine cannot resolve.
- Stage 41 deferred result-return logic is unchanged: returned text is retained and retried until Meboard regains an active `InputConnection`.

## Moonshine compatibility basis
The referenced repository `Today20092/voice-input` currently has:
- base application ID `org.futo.voiceinput`;
- `standalone` flavor suffix `.moonshine`, yielding `org.futo.voiceinput.moonshine`;
- exported `.RecognizeActivity` with an `android.speech.action.RECOGNIZE_SPEECH` intent filter.

Repository master inspected at commit `55dd746510b8ab206449fb2fe59eea13e25a59aa`.

## Artifact
- File: `Meboard-stage42-MOONSHINE-DEFAULT-DEFERRED-COMMIT-TEST.apk`
- SHA-256: `522e1950349cd1a65f829a8d5a03d06d84d23a8f9e2bc551b97b9b9197b0cbb5`
- Bytes: 110029219
- Package: `com.mekromn.meboard`
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

## Exact Stage 41 → Stage 42 package delta
A decompressed-entry comparison of the final signed APKs found:
- changed payloads: `classes.dex` only;
- added payloads: none;
- removed payloads: none;
- `AndroidManifest.xml`, `resources.arsc`, DEX 2–4, assets, and all native libraries are byte-identical to Stage 41.

Fresh signed-output decode comparison found:
- main DEX class count: 7,465 → 7,465;
- changed existing smali classes: exactly one — `com/mekromn/meboard/VoiceProviderRelayActivity.smali`;
- added/deleted smali classes: none;
- DEX 2–4 decoded classes: unchanged.

The only semantic source change is:

```text
org.futo.voiceinput
→ org.futo.voiceinput.moonshine
```

All direct-launch, fallback chooser, Activity result handling, deferred commit, retry timing, and normal mic behavior remain Stage-41 logic.

## Verification
- APK Signature Scheme v3: PASS
- permanent Meboard signer: PASS
- ZIP integrity / 16 KiB native-library alignment: PASS
- fresh signed-output decode: PASS
- Stage-41 payload preservation outside `classes.dex`: PASS
- exact one-class semantic delta: PASS

## Runtime acceptance
1. Short press mic: stock Meboard dictation still works.
2. Long press mic: Moonshine/FUTO Voice Input fork opens directly without the provider chooser.
3. Complete a Moonshine utterance: returned text appears in the original editor.
4. Next short press: stock Meboard dictation still works.
5. If Moonshine is unavailable, long press falls back to Android's system voice-provider chooser.
