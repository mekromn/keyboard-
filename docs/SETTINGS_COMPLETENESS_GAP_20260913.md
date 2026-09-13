# Meboard: settings and reporting-removal coverage gap

Status: confirmed static findings in the delivered Stage-27 APK; no corrected APK issued in this audit. The user reported Stage 27 works, then pointed out that settings for reportedly removed functions remain. General operation feedback is not a complete privacy or dictation test.

## Verified source

- Inspected attachment: `Meboard-stage27-Primes-crash-support-removed-TEST.apk`.
- Actual APK SHA-256 rechecked: `1827fc3a917f28d466f6572e3967acd669f5836df1e8cb2d432adb58c3d66841`.
- Baseline decode identifies Apktool 3.0.3 and that exact APK filename.
- Original compiled `res/xml/setting_privacy.xml` SHA-256: `e795debf76db0ba03643cfd7473dc6c9f333cf2dfd323b4d0b58c9ddab6ced1e`.
- The APK's DEX class definitions and string indexes were independently read to confirm the classes and relevant method-name markers below, rather than relying only on earlier removal reports.
- The unrelated Labs/screenshot request was explicitly withdrawn and is not used as evidence for this audit.

## Actual privacy rows still packaged

The current `setting_privacy.xml` declares all of the following settings. Titles and keys are resolved through the decoded resource table, not guessed from generic Gboard documentation.

| Setting | Stored preference key | Status |
|---|---|---|
| Share usage statistics | `enable_user_metrics` | Row remains, with persistent preference storage; description says keyboard usage statistics are sent to Google. |
| Improve for everyone | `user_enable_federated_training` | Row and federated-learning explanatory text remain. The `evr` shared settings helper still handles its description. |
| Audio donations | `enable_voice_donation` | Auto-synced persistent switch remains, with donation-specific setup/listener and downstream code. |
| Personalize for you | `pref_key_use_personalized_dicts` | Retained local personalization control; not an approved wholesale removal target. |
| Delete learned words and data | `setting_sync_clear_key` | Retained control for clearing local learned data; not an approved wholesale removal target. |

The managed-settings restriction resource `APKTOOL_RENAMED_0x7f170002.xml` also still exposes `enable_user_metrics` and `user_enable_federated_training`. Removing only a visible row would not cover all configuration entry points.

## More than leftover labels

`PrivacySettingsFragment.aB()` selects resource `0x7f170f2c`, which the public resource table identifies as `setting_privacy`. Its `ac()` method locates the donation preference, runs donation-preference setup, constructs an `ewj` listener and assigns it to the preference. The compiled DEX contains the `setupVoiceDonationPref` marker and the fragment class.

`kkl.i(Context, boolean)` writes the donation preference through `qhy`/`cdl.q`, and `kkl.m(Context)` reads it through `cdl.x` with false as the fallback. Both methods are still present; the stored value on the phone has not been read.

The retained `kjo` speech-request construction code calls `kkl.m(Context)`, computes a boolean from it and other conditions, and passes that boolean to `rqw.a(Lztc;ZI)V`. `rqw` identifies itself as `VoiceDonationManager`; its method marker is `maybeAddDonationRequest`. The method still contains opt-in and feature checks, donation counters and donation-request construction. This is a concrete surviving donation-related code path, not merely an unused string. This audit does not establish whether its conditions are met on the user's phone, whether it executed, or whether anything was uploaded. No network capture or external speech-service inspection was performed.

Usage-statistics settings also retain consumers: `psa` reads and observes `enable_user_metrics`, and `psp` identifies itself as `UserMetricsPreferencesCollectionBasisResolver` and reads that setting. Their class definitions are present in the compiled main DEX. Presence and typed references do not establish complete runtime reachability or an active reporting destination.

## Corrected scope of the removal claims

Earlier stages removed specifically listed implementations and narrowly reviewed branches. They did not establish complete end-to-end removal of every reporting feature. Recent stage reports explicitly preserved the manifest and all resources; the privacy settings resource and several settings/consent consumers were therefore not removed by those passes.

The UI remaining alone would not prove that a deleted reporter had returned. However, the settings and donation-code findings above demonstrate a real coverage gap. Describing all related code as gone, or assuring the user that the remaining switches are harmless, would be unsupported. The per-stage class deletions are not invalidated, but they must not be conflated with complete feature removal.

## Required next acceptance boundary

Prioritize the settings-facing reporting paths before presenting more detached-library deletions as completion. For each removed reporting feature, account for its visible row, explanatory/link/promo entry points, preference writes and listeners, managed-settings entries, consumers, request construction and remaining reporting destinations. Remove exclusive code physically, and surgically separate mixed code from retained functionality. Simply hiding the row or setting its value to false does not meet the user's complete-removal standard.

Keep local personalization, learned-data deletion, ordinary recognition/transcription, required feature networking and other retained keyboard behavior. Do not delete shared voice classes wholesale or change microphone/recognition timing as a speculative remedy. The intermittent first-word cutoff remains unresolved/currently not reproducible.

This audit changes documentation and priority only. It applies no APK patch, changes no device setting, captures no audio, and makes no claim of a new signed build. The previously started Stage-28 reporting batch is not completed or delivered by this document. Privacy-final remains false.
