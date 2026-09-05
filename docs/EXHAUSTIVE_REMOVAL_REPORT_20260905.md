# Meboard exhaustive removal and preservation report

**Report generated:** 2026-09-05T16:01:17.625358+00:00

## Scope and exact build

This report describes the signed Meboard candidate delivered immediately before the user reported that the keyboard appears on the Pixel 9 Pro XL. A device-side re-read of the installed base-APK SHA has not yet been completed, so the runtime report is attributed to this candidate by sequence, not claimed as an independently re-hashed installation. It is not a generic plan and it does not attribute later experimental removals to this build.

- Current candidate: `Meboard-stage16-density-resource-fix-replay-signed.apk`
- Candidate SHA-256: `913b5e69997541ad6015d80661677f510826cfd63980b85a9178a95b71780342`
- Package: `com.mekromn.meboard`
- Build lineage: Stage 16 + signature guard repair + density-resource repair
- User-confirmed runtime state: Keyboard renders; Meboard settings confirmed working; exhaustive feature sweep pending
- Privacy-certified/final: **NO**
- Original source bundle SHA-256: `665e4fb3c04874037c1b6477ef734fb38934e300a4f4197978dd6d4c72d28a10`

> Critical scope boundary: the later Stage 18 `remove_mozc_telemetry_complete.py` pass exists in the repository, but it is **not part of the tested Stage-16 APK covered by this report**. Full Stage-18 Mozc telemetry removal is therefore listed as pending, not credited as completed.

## Verified quantitative ledger

- Original smali classes: **22,050**
- Final smali classes: **21,776**
- Classes physically deleted: **274**
- Classes added: **0**
- Surviving classes with non-branding code changes: **136**
- Identity/branding-only changed classes: **13**
- Fields physically removed from surviving classes: **261**
- Methods physically removed from surviving classes: **77**
- Reduced/replacement signatures introduced to remove telemetry parameters: **11**
- Surviving method bodies changed: **167**
- Manifest component registrations removed: **24**
- Registrations plus implementation classes both deleted: **15**
- Registrations removed while implementation remains packaged: **9**
- Manifest permissions removed: **1** (`GET_ACCOUNTS`)
- Manifest metadata entries removed: **29**
- Dedicated native crash library removed: **1**
- Brella/TensorFlow feature split omitted: **1**

The complete 112 KB report, 308 KB machine-readable ledger, exact 274-class list, all 261 field removals, all 77 removed methods, all 167 changed method bodies, manifest tables, native/split inventory, and independent verification are stored in the persistent Library checkpoint:

`/Meboard/Checkpoints/20260905T135810Z`

## Removal summary

### Account identity and profiling

Physically removed the account-status graph (`mph`, `moz`, `mpo`, `ksg`, `mpi`, `mpb`–`mpe`, `AccountsCapabilitiesChangedReceiver`), direct `AccountManager` account-name enumeration, the GMS `get_accounts` bypass, Email-LM account seeding, Mozc self-account import, account capability/age/profile classification, Google-account feedback identity, account-listener lifecycle, `GET_ACCOUNTS`, and account/Phenotype registrations. Email LM, Mozc, local learning, downloads, and anonymous feedback remain.

### Clearcut and Primes

Removed the LatinApp metrics-factory startup block; 44 initial module roots; generated provider switch cases; 48 dead Dagger module/interface classes; LegacyClearcutAdapter; the detached Clearcut forwarding wrapper; Primes processors and flag providers; network/cache metric callbacks and constructor parameters; the telemetry interceptor; NativeCrashHandlerImpl; LifeboatReceiver; ClearcutMetricSnapshotTransmitter; the dedicated native crash-handler JNI library; and Cronet telemetry opt-in. Retained actual transports and user-triggered networking.

### Federated learning, Brella, and training caches

Omitted the Brella split and `libtensorflow_jni.so`; removed DynamicTrainer; `NativeFLRunnerWrapper`; the federated service branch and `runFlTraining` API/Binder transaction; InAppTrainingService; ExampleStoreServiceMultiplexer; FederatedResultHandlingService; training-cache guards, maintainers, metrics, statistics, managers, Java collection/export processors, and example-store registrations. Retained local computation and `NativeLCRunnerWrapper` where needed for local AI.

### Remote Phenotype

Removed remote fetch/update classes and callbacks, forced BackupAgent fetches, account/update receivers, metadata holder, and 24 binary/XML Phenotype registrations plus heterodyne metadata. Retained bundled/static defaults.

### Feature-attached reporting

Removed reporting processors/helpers and logger lifecycle from Apostrophe promo, Agentic Dictation, Clipboard, SignBoard, Delight KLP downloader, Device Intelligence, SuperInsert, Handwriting, Latin5/Delight5, Jarvis, Undo, Free Cursor, companion/widget, expression/emoji, post-correction, InputMethodEntry, DailyPing, DefaultCounter, and 23 detached processor/helper pairs. The corresponding feature implementations were intended to remain.

### Keyhound

Removed the hidden input-data collection/export module, including its provider and 12 helper classes, registry/factory branches, dump constructors/callables, private-command markers, and input-action path resource. This removed input/action, audio-command, stylus/Scribe, and Mozc dump/export behavior without removing the input engines.

### Perfetto/debug/reporting

Removed the Java Perfetto trigger cluster, cold-start trace provider, web debug provider, WorkManager diagnostics receiver, SwissArmyKnife diagnostic file provider, package-stats callback, and obsolete missing-splits activity.

### Coexistence and signature guard

Rebased the package to `com.mekromn.meboard`, removed the legacy `original-package` alias and split/core-app assumptions, rebased authorities/permissions/self URIs, and removed the Google-certificate whitelist scheduler, comparator, exception branch, and four embedded certificate digests. Android Package Manager signer enforcement remains.

## Important non-final findings

The build is **not privacy-final**:

1. `libintegrated_shared_object.so` is byte-identical to source and still contains native metrics, training-cache, federated-predictor, playlog, and Perfetto symbols/strings. A broad marker is not proof of reachability, but native physical removal is unfinished.
2. Nine component registrations were removed while their implementation classes remain packaged.
3. `LocalComputationResultHandlingService` lost its manifest registration even though local computation is a retained requirement. This is the highest-priority potential over-removal and must be tested/analyzed.
4. `ImageFeedbackActivity`, `DecoderStateReportActivity`, and `QualityBugReportActivity` also lost registrations. Because explicit anonymous feedback was supposed to remain, these may be broader than intended.
5. GMS `InAppTrainingServiceImpl` and local-computation-related classes remain and require source-to-sink classification.
6. Dictation, Tenor/GIF, downloads, translation, and feedback retain networking and still need runtime capture proving it is user-triggered and free of passive telemetry/account/model data.
7. The later complete Mozc telemetry pass is not in the tested Stage-16 APK.
8. Full feature regression, idle-network capture, and ordinary-typing network capture remain pending.

This compact GitHub document records the authoritative findings without publishing the proprietary APK, source bytes, signing material, or private full ledger. The full audit files remain in the private Library checkpoint.