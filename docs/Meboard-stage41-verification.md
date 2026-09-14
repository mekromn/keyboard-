# Meboard Stage 41 — FUTO default + deferred result commit

Status: signed test APK; static/build verification PASS; phone runtime pending.

## Runtime goals
- Short mic tap remains the existing Meboard/Gboard voice path.
- Long mic press keeps the Stage-39/40 distinct long-press route.
- FUTO Voice Input (`org.futo.voiceinput`) is launched directly for `android.speech.action.RECOGNIZE_SPEECH` when installed.
- Android's system chooser is used only as a fallback if FUTO cannot resolve.
- Returned recognition text is not committed immediately while the relay activity still owns focus. It is retained and retried after the relay closes.
- Commit retries first use `InputMethodService.getCurrentInputConnection()`, then the pre-launch cached connection, every 150 ms after an initial 300 ms delay, for a bounded 30 retries.

## FUTO compatibility basis
The current FUTO Voice Input manifest exposes exported `RecognizeActivity` for `android.speech.action.RECOGNIZE_SPEECH` under package `org.futo.voiceinput`, and FUTO returns text through `RecognizerIntent.EXTRA_RESULTS` with `RESULT_OK`.

## Artifact
- File: `Meboard-stage41-FUTO-DEFAULT-DEFERRED-COMMIT-TEST.apk`
- SHA-256: `f53dfac88377c5490b40459a31fa9dce651b5922eb4987fdf7d56107c7747678`
- Bytes: 110111139
- Package: `com.mekromn.meboard`
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

## Exact Stage-40 → Stage-41 package delta
A decompressed-entry comparison of the final signed APKs found:
- changed payloads: `classes.dex` only
- added payloads: none
- removed payloads: none
- `AndroidManifest.xml`, `resources.arsc`, DEX 2–4, assets, and all native libraries are byte-identical to Stage 40.

Final signed APK was freshly decoded after signing. It contains:
- direct FUTO package targeting in `VoiceProviderRelayActivity`;
- fallback system chooser;
- `VoiceProviderChooser.deferResults(...)`;
- bounded `tryCommitPending(...)` retry logic;
- `VoiceResultCommitRunnable`.

## Verification
- APK Signature Scheme v3: PASS
- permanent Meboard signer: PASS
- ZIP integrity / 16 KiB native-library alignment: PASS
- fresh signed-output decode: PASS
- Stage-40 payload preservation outside `classes.dex`: PASS

## Runtime acceptance
1. Short press mic: stock Meboard dictation still works.
2. Long press mic: FUTO opens directly without the provider chooser.
3. Complete a FUTO utterance: returned text appears in the original editor.
4. Next short press: stock Meboard dictation still works.
5. If FUTO is unavailable, long press falls back to Android's system voice-provider chooser.
