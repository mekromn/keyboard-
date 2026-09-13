# Meboard Stage 28 — privacy controls and direct audio-donation sink removal

Date: 2026-09-13. Status: **signed test APK; bounded static/build checks PASS; phone runtime pending; privacy-final NO**.

## Exact artifact and rollback

- New APK: `Meboard-stage28-Privacy-controls-donation-sink-removed-TEST.apk`
- SHA-256: `35e76d5b03ce66983f8fba5de6b36b357919ad702c18d74bcc57f810e8df1d3e`
- Size: **110099372 bytes**.
- Package: `com.mekromn.meboard`.
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`.
- Exact Stage-27 input/rollback SHA-256: `1827fc3a917f28d466f6572e3967acd669f5836df1e8cb2d432adb58c3d66841`.
- Stage-28 branch: `meboard/stage28-privacy-controls-test-20260913`.

The user confirmed Stage 27 works before requesting the settings-completeness cleanup. This is general operation feedback, not a network audit or installed-device readback. Stage 27 remains the rollback.

## What this pass physically removes

### Privacy UI / managed configuration

The visible Privacy screen no longer contains:

- **Share usage statistics** (`enable_user_metrics`)
- **Improve for everyone** (`user_enable_federated_training`)
- **Audio donations** (`enable_voice_donation`)

The managed-configuration XML also no longer contains `enable_user_metrics` or `user_enable_federated_training` restrictions.

The retained Privacy screen still contains:

- **Personalize for you** (`pref_key_use_personalized_dicts`)
- **Delete learned words and data** (`setting_sync_clear_key`)

### Direct audio-donation request sink

The dedicated `rqw` / `VoiceDonationManager` class is physically deleted. Its `maybeAddDonationRequest` implementation and donation-message attachment are absent. The request-builder wiring is removed from both retained call paths:

- `kjo` S3 request mutation path
- `smc` retained speech/request builder path

The `rqw` fields and constructor wiring are removed from `kjr` and `smc`.

### Settings listener/setup

`PrivacySettingsFragment.ac()` no longer looks up or configures the audio-donation preference. It now only forwards to its superclass setup. The donation-only `PrivacySettingsFragment.aD(boolean)` callback is deleted. Its two now-unreachable `eke` runnable cases (selectors 18 and 19) are physically removed from the shared synthetic dispatcher; the other 18 cases remain.

## Exact code/resource boundary

Decoded Stage-27 -> Stage-28 delta:

- Deleted class: `rqw` (`VoiceDonationManager`)
- Modified classes: `PrivacySettingsFragment`, `eke`, `kjr`, `kjo`, `smc`
- Modified resources: `res/xml/setting_privacy.xml`, `res/xml/APKTOOL_RENAMED_0x7f170002.xml`

Fresh decode of the signed Stage-28 APK confirms class count **21745 -> 21744**, exactly one deleted class, no added classes, and only those five surviving class files changed.

The final APK was packaged from the exact Stage-27 payload rather than accepting Apktool's broader resource canonicalization. Its non-signature payload entry set is therefore preserved exactly: **9148 entries before and after**. Only four APK payload entries differ:

1. `classes2.dex`
2. `resources.arsc`
3. `res/xml/setting_privacy.xml`
4. `res/xml/APKTOOL_RENAMED_0x7f170002.xml`

The other **9144 entries are byte-identical**, including the manifest, all 16 native libraries, other DEX files, dictionaries, dictation library, Tenor library and other resources.

## Verification performed

- APK SHA-256 rechecked after signing.
- Original Meboard signer certificate preserved.
- APK Signature Scheme v3: verified.
- 16-KiB native-library alignment / 4-byte stored-entry alignment: verified by the existing build tools.
- ZIP CRC: PASS.
- Exact 9148-entry payload set preserved.
- Native libraries: all byte-identical to Stage 27.
- Fresh signed-output decode confirms `rqw`, `VoiceDonationManager`, `maybeAddDonationRequest`, and `PrivacySettingsFragment.aD(boolean)` references absent.
- Privacy XML confirms all three target sharing rows absent and both retained local controls present.
- Managed restrictions confirm usage-metrics and federated-training controls absent.
- `res/values/public.xml` is byte-identical to Stage 27, preserving public resource IDs.
- `AndroidManifest.xml` is byte-identical to Stage 27.
- `eqt.aI()` register-state verifier PASS; `v13=0` and `v17=15` preserved.
- Core voice/recognizer decoded classes `kgm`, `kgw`, `kht`, `kjp`, `kjm`, `kig`, `fct`, `ruo`, and `rrf` are byte-identical to Stage 27.

These are static/build checks, **not Android runtime tests or network capture**.

## Important limit — cleanup is not complete

This stage deliberately does **not** claim complete removal of all reporting/privacy code. In particular, the Stage-27 audit found additional code still to classify/remove:

- usage-metrics preference/collection-basis backend (`psa`, `psp` and mixed consumers);
- federated/training remnants beyond the removed setting surface;
- voice-donation promo/consent/preference helpers (`kgd` ecosystem and donation-related `kkl` methods) that no longer have the direct `VoiceDonationManager` request sink removed here;
- other Primes/diagnostic, Phenotype, unresolved networking and native reporting code.

Those are the next cleanup targets. Merely having the rows gone is not being treated as complete removal.

## Voice behavior

No core recognizer, microphone, timeout, dictation engine or voice-provider routing code was changed. The earlier first-word cutoff remains open/currently not reproducible. Stage 28 is **not** a voice-fix build.

## Future feature phase

After the privacy cleanup is complete, the queued feature phase remains:

- black glassmorphic translucent/blurred keyboard theme with an opaque dark fallback when true blur is unavailable;
- normal microphone tap must preserve the existing standard dictation path;
- microphone long press opens an explicit alternate speech-to-text provider chooser, without also triggering the normal tap.

Those features are intentionally not mixed into Stage 28 so privacy and runtime regressions remain attributable.
