# Stage 31a failed runtime checkpoint

User report on 2026-09-13: Stage 31a still crashes when launched from the installer. Do not promote Stage 31 or Stage 31a. Stage 27 remains the last user-confirmed working rollback.

Static re-analysis found that the first Stage-31a repair fixed only the normal late path in `oup.onStartInput(EditorInfo, boolean)`. An existing early stock `goto :goto_4` can still reach the added Meboard glass refresh before local register `v14` has been defined, so ART can reject the method/class during verification.

No claim is made that this user-visible crash was captured with a device stack trace in this turn; the verifier defect is independently reproducible from the exact signed Stage-31a APK by definite-register dataflow.
