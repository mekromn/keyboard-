# Meboard voice regression — 2026-09-12

Status: **OPEN — intermittent, currently not reproducible by the user; root cause unconfirmed; no repaired APK issued**.

## Latest user observation — 20:56:31 UTC

The user reported: "I can't reproduce it it seems to be working fine now".

This supersedes the active-failure status, but does not establish a root cause or a verified fix. No failure log, installed-APK readback, or new phone-side test evidence was supplied with this observation. The user did not say whether they had installed the suggested Stage-21 rollback, so the current installed build must not be assumed to be Stage 22 or Stage 21.

Keep the currently working installation unchanged. No forced reproduction, data clearing, or rollback is requested while voice input is behaving normally. The existing one-shot capture is useful if the problem recurs; it need not be run merely to produce a report now. On recurrence, record whether the microphone switches off or stays listening while text updates stop.

No speculative changes to dictation timeouts, microphone handling, account isolation, or recognizer routing are justified by this observation. This update changes documentation only: no APK is modified, no removal stage is advanced, and no build is newly promoted or voice-certified. The issue remains open for regression tracking rather than being marked fixed.

## Original report — 20:10:57 UTC

The user reported: "Voice to text is broken it stops after the first word sometimes". This report followed delivery of Stage 22. The installed APK was not read back; temporal sequence alone does not prove Stage 22 introduced the issue. Previous "works" reports are general operation feedback, not continuous-dictation certification. Removal progression was paused when the report arrived.

## Initial investigation already recorded

The delivered Stage-21 and Stage-22 APK files were recovered from current-conversation attachments and independently SHA-256 checked. Both were decoded with the recovered pinned Apktool 3.0.3. The pristine Gboard base.apk was recovered from the saved original ASPK and independently decoded for voice-code comparison. These checks belong to the initial investigation, not a new audit performed for the 20:56:31 update.

- Stage 21: `c83284fd77f0a99667f39530441ee10391cf185add1cc6e1d64378ba59b41d0e`, 110132140 bytes.
- Stage 22: `8cf20fabd5ccba93aae7187fa27f4ffe3cbb3bed37a42c73d1e7c34c65db4766`, 110132140 bytes.
- Stage-21 to Stage-22 comparison: exactly `lnk`, `lcw`, and `lna` changed, with no added/deleted class files; 21761 classes in each.
- Only `classes.dex` and `classes2.dex` differ as decompressed APK payloads. All 16 packaged native libraries are unchanged between these builds.

Nine inspected decoded class files in Stage 22 are byte-identical to the decoded pristine base: `kgm` (VoiceInputHandler), `kgw` (VoiceInputManager), `kht` (MicrophoneInputStreamWrapper), `kjp` (SpeechRecognizerListener), `kjm` (NewS3Recognizer), `kig` (SodaRecognizerWrapper), `fct` (JetsonLiteRecognizer), `ruo` (SmartDictation), and `rrf` (voice-stop reasons).

This is bounded static evidence, **not proof of correct voice behavior**. Earlier edits touched AgenticDictationExtension (`fbl`) metrics wiring and shared synthetic classes. Account/config changes, shared dependencies, asynchronous failures, recognizer routing, microphone lifecycle, or external speech service behavior have not been excluded. There is no runtime evidence yet selecting one of those possibilities.

## Existing diagnostic points

The inspected code retains logging calls for:

- `VoiceInputManager.stopListeningVoice` with a reason.
- `VoiceInputManager.stopVoiceInput` with state and reason.
- `SpeechRecognizerListener.onEndOfSpeech`, `onError`, `onRecognitionFinished`, and `onRecognitionTerminated`.

Presence of these calls does not guarantee all messages are emitted or still in Android's log buffer. A first word appearing alone does not establish whether listening stopped, recognition failed, the input connection changed, or text updates stalled. Do not change silence thresholds, restart recognition in a loop, restore account access, enable reporting, or force cloud recognition based on this symptom alone.

## One-shot local capture, only if the problem recurs

`tools/capture_meboard_voice.sh` reads recent existing main/system/crash log messages filtered to the installed Meboard app UID. It also attempts to hash the installed base APK. Run it in LADB or an authorized ADB shell immediately after an actual failure when practical; use harmless test text.

It does not record audio, read learned models, clear app data/logs, change settings/permissions, or upload files. Existing app logs may contain recognized text or other sensitive app data: review before sharing. It refuses an unfiltered fallback when the UID cannot be resolved. External speech-service and system-process messages are deliberately not included, so an empty or insufficient capture is not a clean bill of health.

The shell script passed `sh -n` and four mocked shell cases during the initial investigation: successful UID-filtered output, unresolved UID refusal, non-ADB-shell refusal, and logcat-error propagation. It has not been executed on an Android device as part of the recorded investigation.

## Rollback and acceptance

The original Stage-21 APK remains available as the immediate rollback/A-B candidate, not as a newly fixed APK and not as a voice-certified build. The latest user observation does not require a rollback. If the issue recurs and an A/B test is needed, retain failure evidence first when practical and do not uninstall or clear Meboard data. If Stage 21 also fails, the issue is not isolated to the Stage-22 delta. One successful utterance is not sufficient to clear an intermittent failure.

Preserve all existing working/checkpoint branches and signed APKs. This branch adds diagnostic documentation/tooling only; no APK is modified or newly signed. Local AI, essential feature networking, account isolation and removal policy remain unchanged. Privacy-final remains false.
