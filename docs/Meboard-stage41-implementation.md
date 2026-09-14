# Stage 41 implementation notes

Base: Stage 40 (`meboard/stage40-android-system-voice-provider-chooser-test-20260914`).

## Direct FUTO default
`VoiceProviderRelayActivity` still launches `android.speech.action.RECOGNIZE_SPEECH`, but first scopes the Intent to package `org.futo.voiceinput`. If that scoped Intent resolves, it is launched directly with `startActivityForResult`. If it does not resolve, the package scope is removed by constructing a fresh generic recognition Intent and Android's system chooser is used as fallback.

This preserves Stage 40's one-shot behavior: normal Meboard mic taps are unchanged; only the already-distinct long-press path uses FUTO.

## Deferred text return
Stage 40 attempted to commit returned recognition text immediately while the transparent relay/FUTO activity flow still owned focus. Stage 41 instead stores the first returned `RecognizerIntent.EXTRA_RESULTS` string as pending and schedules a delayed main-thread commit.

Commit order per retry:
1. `InputMethodService.getCurrentInputConnection()` after the original editor/IME regains focus.
2. The pre-launch cached `InputConnection` as a fallback.
3. If neither commit succeeds, retry every 150 ms for up to 30 retries after an initial 300 ms delay.
4. Clear the pending result only after `commitText()` succeeds or the bounded retry window expires.

New helper: `com.mekromn.meboard.VoiceResultCommitRunnable`.

## Binary boundary
Final signed Stage 40 → Stage 41 decompressed payload comparison: only `classes.dex` changed. Manifest, resources, DEX 2–4, assets, and native libraries remain byte-identical.

No signing material is stored in this repository.
