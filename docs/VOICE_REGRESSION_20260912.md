# Meboard voice regression — 2026-09-12

Status: **BLOCKER — root cause not established; no repaired APK issued**.

The user reported at 20:10:57 UTC: "Voice to text is broken it stops after the first word sometimes". This report followed delivery of Stage 22. The installed APK was not read back; temporal sequence alone does not prove Stage 22 introduced the issue. Previous "works" reports are general operation feedback, not continuous-dictation certification. Do not promote Stage 22 or advance privacy removals until the voice regression is diagnosed.

## Fresh work performed in this turn

The delivered Stage-21 and Stage-22 APK files were recovered from current-conversation attachments and independently SHA-256 checked. Both were decoded with the recovered pinned Apktool 3.0.3. The pristine Gboard base.apk was recovered from the saved original ASPK and independently decoded for voice-code comparison.

- Stage 21: `c83284fd77f0a99667f39530441ee10391cf185add1cc6e1d64378ba59b41d0e`, 110132140 bytes.
- Stage 22: `8cf20fabd5ccba93aae7187fa27f4ffe3cbb3bed37a42c73d1e7c34c65db4766`, 110132140 bytes.
- Fresh Stage-21 to Stage-22 comparison: exactly `lnk`, `lcw`, and `lna` changed, with no added/deleted class files; 21761 classes in each.
- Only `classes.dex` and `classes2.dex` differ as decompressed APK payloads. All 16 packaged native libraries are unchanged between these builds.

Nine inspected decoded class files in Stage 22 are byte-identical to the decoded pristine base: `kgm` (VoiceInputHandler), `kgw` (VoiceInputManager), `kht` (MicrophoneInputStreamWrapper), `kjp` (SpeechRecognizerListener), `kjm` (NewS3Recognizer), `kig` (SodaRecognizerWrapper), `fct` (JetsonLiteRecognizer), `ruo` (SmartDictation), and `rrf` (voice-stop reasons).

This is bounded static evidence, **not proof of correct voice behavior**. Earlier edits touched AgenticDictationExtension (`fbl`) metrics wiring and shared synthetic classes. Account/config changes, shared dependencies, asynchronous failures, recognizer routing, microphone lifecycle, or external speech service behavior have not been excluded. There is no runtime evidence yet selecting one of those possibilities.

## Existing diagnostic points

The inspected current code retains logging calls for:

- `VoiceInputManager.stopListeningVoice` with a reason.
- `VoiceInputManager.stopVoiceInput` with state and reason.
- `SpeechRecognizerListener.onEndOfSpeech`, `onError`, `onRecognitionFinished`, and `onRecognitionTerminated`.

Presence of these calls does not guarantee all messages are emitted or still in Android's log buffer. A first word appearing alone does not establish whether listening stopped, recognition failed, the input connection changed, or text updates stalled. Do not change silence thresholds, restart recognition in a loop, restore account access, enable reporting, or force cloud recognition based on this symptom alone.

## One-shot local capture

`tools/capture_meboard_voice.sh` reads recent existing main/system/crash log messages filtered to the installed Meboard app UID. It also attempts to hash the installed base APK. Run it in LADB or an authorized ADB shell immediately after reproducing the failure with a harmless sentence.

It does not record audio, read learned models, clear app data/logs, change settings/permissions, or upload files. Existing app logs may contain recognized text or other sensitive app data: review before sharing. It refuses an unfiltered fallback when the UID cannot be resolved. External speech-service and system-process messages are deliberately not included, so an empty or insufficient capture is not a clean bill of health.

The shell script passed `sh -n` and four mocked shell cases: successful UID-filtered output, unresolved UID refusal, non-ADB-shell refusal, and logcat-error propagation. It has **not** been executed on an Android device in this turn.

## Rollback and acceptance

The original Stage-21 APK is available as the immediate rollback/A-B candidate, not as a newly fixed APK and not as a voice-certified build. Capture Stage-22 failure evidence first when practical, then test Stage 21 over the existing same-signer installation without uninstalling or clearing data. If Stage 21 also fails, the regression predates Stage 22 or has another dependency; do not claim an isolated Stage-22 cause. One successful utterance is not sufficient to clear an intermittent failure.

Preserve all existing working/checkpoint branches and signed APKs. This branch adds diagnostic documentation/tooling only; no APK is modified or newly signed. Local AI, essential feature networking, account isolation and removal policy remain unchanged. Privacy-final remains false.
