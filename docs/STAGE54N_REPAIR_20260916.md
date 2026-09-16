# Stage 54n

Repairs the three Stage 54m device-test failures without replacing any stock theme.

- Appends `Meboard Transparent` as a second labeled theme tile after `Meboard`; stock theme entries are unchanged.
- Keeps normal `Meboard` as the no-saved-theme default fallback; Transparent is selectable only.
- Voice typing sound control now explicitly mirrors the visible switch state into the SharedPreferences store used by the VoiceSoundManager gate, including restored state after preference attachment.
- Emoji long-press classification now uses the live logical SoftKeyDef IDs (`0x7f0b2527`, `0x7f0b2528`, `0x7f0b252a`, `0x7f0b252b`) with the stock smiley/emoticon view IDs retained as fallback.
- APK delta vs 54m: only `classes2.dex` plus version metadata.

Artifact SHA-256: `a3fea209b96d3d32f18adee3131dfedb393a8d7eee6af61a5e21d7677c20e655`.
