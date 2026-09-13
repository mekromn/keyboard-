# Meboard feature phase after privacy cleanup

Requested by the user on 2026-09-13 at 06:32:32 UTC while the settings/reporting cleanup was in progress. These are queued requirements, not implemented features or a released build.

## Black glass theme

The keyboard theme should be black, glass-like, translucent/transparent, with a blurred background. Preserve readable keys and suggestions, touch targets, typing responsiveness, and feature layout. Real background blur must be validated on the target Pixel/Android IME window; a merely translucent fill must not be described as working background blur. Keep an opaque dark fallback when actual blur is unavailable. Opacity and blur strength are candidate controls, not an additional user requirement.

## Microphone gesture contract

- A regular tap must follow the existing standard speech-to-text path exactly as it does now. No provider chooser, added delay, or changed default provider on a normal tap.
- A long press opens a chooser for alternative voice-to-text providers.
- Consuming a long press must not also trigger the ordinary microphone tap. Cancelling the chooser must not start recording.
- Available providers and their offline/network behavior must be established before offering them. Do not assume every installed app supplies a compatible recognizer. Additional providers must not silently restore account discovery, audio donation, analytics, or model/learned-data uploads.
- Selecting an alternate provider is an explicit user action. The request does not authorize making it the permanent normal-tap default.

## Ordering and status

Finish the current privacy-settings and connected reporting/donation removal work first. Keep visual and recognizer feature changes in separate test builds so regressions can be attributed. Preserve local personalization, learned-data deletion and normal dictation. The earlier intermittent first-word cutoff remains unresolved/currently not reproducible, not certified fixed by these future features.

This document changes no APK, device setting, or voice route.
