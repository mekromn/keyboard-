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

Contains a ~34.8 MB TensorFlow native library. Because the base APK also exposes federated-learning/training integration, this split is a prime candidate for complete removal if no retained user-facing feature depends on it. Removal means deleting the split and all base-APK integration code, registrations, schedulers, result handlers, storage, and references to that system.

### Dictation split

Contains `libdictation_jni.so`. Preserve only if voice typing is intentionally retained. Its networking must be audited separately so only code required for active dictation remains; unrelated telemetry/metrics inside the dictation path must still be removed.

### Tenor animation split

Contains `libtenoranimation_jni.so`; base strings expose Tenor server URL settings. Preserve only if GIF/sticker search is desired. Traffic must only occur as a direct consequence of explicit user interaction, and any analytics/metrics code around Tenor remains subject to physical removal.

## Physical removal policy

The privacy build must physically remove these categories from code, not merely disable them:

1. Analytics / metrics upload clients.
2. Clearcut logging implementations, registration, queues, persistence, serialization, scheduling, and transport.
3. Primes telemetry collection/reporting code, including network/performance metric upload paths.
4. Background crash/diagnostics collection and upload code that is not required for local crash safety.
5. Federated learning/background training code, transport, eligibility logic, schedulers, result handlers, caches, and Brella integration.
6. The Brella feature split and every base/split reference to it unless a separately justified retained feature requires part of it.
7. Nonessential Phenotype/remote-experiment polling, receivers, fetch/update clients, persistence, and experiment-selection logic. Required feature defaults should become local constants/data without retaining the remote configuration machinery.
8. Feedback/survey upload implementations unless a deliberately retained user-triggered feature truly requires them.
9. Background network jobs/services/receivers whose purpose is telemetry, experimentation, diagnostics, training, profiling, or unsolicited synchronization.
10. Telemetry-specific Perfetto/trace triggering and telemetry-specific native crash reporting paths.

### Not acceptable

The following are explicitly rejected as incomplete:

- `enabled = false` / preference gates.
- No-op replacement methods/classes.
- Early `return` patches.
- Empty service/receiver shells.
- Hostname replacement, DNS blocking, firewall rules, or certificate failures.
- Removing only manifest entries while DEX/native implementations remain.
- Leaving dead/unreachable telemetry classes or methods packaged in the APK.
- Renaming symbols while retaining telemetry behavior.

### Shared-code rule

When a class mixes required keyboard functionality with telemetry, do not delete the required class wholesale. Instead remove the telemetry-specific fields, methods, branches, callbacks, registration, serialization, persistence, scheduling, and transport code from that shared class, then remove newly dead telemetry dependencies recursively.

## Preserve deliberately

Do not blindly remove `INTERNET` or every HTTP stack. Networking is retained only when it is required for a feature the project explicitly chooses to keep, for example:

- Explicit language/model downloads.
- Voice/dictation while actively used.
- GIF/sticker/emoji online lookup when explicitly invoked.
- Other clearly user-triggered online features that are intentionally retained.

Any analytics, metrics, diagnostics, experimentation, or unsolicited background networking attached to those retained features is still removed.

## Verification requirements

A cleanup is not complete until all of the following are checked:

- Rebuilt APK/splits install successfully and use one consistent signing key.
- Keyboard launches, can be enabled as an IME, and types normally.
- No startup crash from removed dependencies.
- Static decoded-tree scan finds no targeted telemetry classes/methods/registrations/components.
- Static binary scan finds no targeted telemetry implementation markers in DEX/native code, except documented false positives that contain no executable telemetry behavior.
- Manifest contains no removed telemetry services, receivers, providers, jobs, or telemetry-specific metadata.
- No telemetry-only feature split is shipped.
- Runtime network capture shows no unsolicited traffic while idle and during ordinary offline typing.
- User-triggered retained online features still work only when invoked.
- Background jobs/services for removed telemetry/training systems do not run.
- Code-size/class-count deltas are recorded so physical removal is measurable rather than asserted.

## Current limitation

The ChatGPT execution environment used for the initial audit did not include Apktool/apksigner and could not reach GitHub release assets from the container network, so the initial repository commits record the exact removal surface and verification tooling rather than pretending a hostname-only edit constitutes a finished privacy build.
