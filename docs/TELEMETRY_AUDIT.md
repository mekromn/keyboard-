# Telemetry / network audit

Target: Gboard 18.0.3.954559732 arm64-v8a bundle supplied by the project owner.

## Bundle layout

- `base.apk` (~88.9 MB)
- `split_brella_feature_split.apk` (~34.8 MB)
- `split_dictation_feature_split.apk` (~4.36 MB)
- `split_tenoranimation_feature_split.apk` (~11.64 MB)
- `split_config.xxhdpi.apk`

## High-confidence privacy surfaces found in the base APK

Static DEX-string inspection found explicit references to:

- Google Clearcut metrics/logging.
- Primes performance/network metrics, including `recordNetworkMetricsToPrimes`.
- Phenotype flags/configuration and update handling.
- Federated-learning/background-training code paths.
- `FederatedResultHandlingService`-related behavior / training-result handling.
- Brella integration (`BRELLA_SQL_HANDLED_INSIDE_MODULE`).
- Training caches / experiment IDs.
- Perfetto trace triggering.
- Native crash handling / crash-recovery metrics.
- Numerous keyboard-specific `MetricsProcessor` implementations.
- `android.net.http.EnableTelemetry`.
- Feedback upload plumbing.

Representative strings observed include:

```
PHENOTYPE
Fetch and update phenotype flags
com.google.android.gms.phenotype
Primes version: %d
recordNetworkMetricsToPrimes
primes.packageMetric.lastSendTime
BRELLA_SQL_HANDLED_INSIDE_MODULE
FederatedLearning_TrainingEligible
training_cache_experiment_id_list
android.net.http.EnableTelemetry
Failed to read native crash dir.
Triggering Perfetto trace for %s
```

## Split assessment

### Brella split

Contains a ~34.8 MB TensorFlow native library. Because the base APK also exposes federated-learning/training integration, this split is a prime candidate for complete exclusion in a privacy build if no retained user-facing feature depends on it.

### Dictation split

Contains `libdictation_jni.so`. Do **not** remove by default if voice typing is to remain functional. Audit its transport separately and gate it behind explicit dictation use.

### Tenor animation split

Contains `libtenoranimation_jni.so`; base strings expose Tenor server URL settings. Preserve only if GIF/sticker search is desired, and ensure traffic occurs only as a direct consequence of user interaction.

## Removal policy

The privacy build should remove or hard-disable these categories rather than merely blocking domains:

1. Analytics / metrics upload clients.
2. Clearcut logging paths.
3. Primes collection and network metrics reporting.
4. Background crash/diagnostics upload.
5. Federated learning/background training transport and scheduling.
6. Brella feature split when no retained feature requires it.
7. Nonessential Phenotype polling/update receivers and remote experiment fetches; replace with deterministic local defaults where required for stability.
8. Feedback/survey upload paths unless explicitly invoked by the user.
9. Background network jobs/services/receivers whose only purpose is telemetry, experiments, training, diagnostics, or unsolicited synchronization.

## Preserve deliberately

Do not blindly remove `INTERNET` or all HTTP stacks. Gboard includes legitimate optional features that can require networking. Preserve only the minimum paths needed for features the owner chooses to retain, such as:

- Explicit language/model downloads.
- Voice/dictation while actively used.
- GIF/sticker/emoji online lookup when explicitly used.
- Other clearly user-triggered online features.

## Verification requirements

A cleanup is not complete until all of the following are checked:

- Rebuilt APK/splits install successfully and use one consistent signing key.
- Keyboard launches, can be enabled as an IME, and types normally.
- No startup crash from removed flag/config dependencies.
- Static scan no longer finds active telemetry component registrations and targeted upload call paths.
- Runtime network capture shows no unsolicited traffic while idle and during ordinary offline typing.
- User-triggered retained online features still work only when invoked.
- Background jobs/services for removed telemetry/training systems do not run.

## Current limitation

The ChatGPT execution environment used for the initial audit did not include Apktool/apksigner and could not reach GitHub release assets from the container network, so this first commit records the exact removal surface and reproducible audit tooling rather than pretending a hostname-only edit constitutes a finished privacy build.
