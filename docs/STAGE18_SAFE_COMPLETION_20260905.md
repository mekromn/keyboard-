# Meboard Stage 18 safe completion boundary — 2026-09-05

This branch advances from the user-confirmed keyboard-rendering density-resource
checkpoint. It does not overwrite that immutable recovery point.

## Restored retained entry points

The exhaustive Stage-16 comparison found four broad manifest removals whose
implementations remained intact and belonged to the retained feature contract:

- `LocalComputationResultHandlingService`
- `ImageFeedbackActivity`
- `DecoderStateReportActivity`
- `QualityBugReportActivity`

`tools/restore_retained_manifest_entrypoints.py` restores their exact upstream
manifest elements and rebases only package-bound values to Meboard. It verifies
that each implementation exists and that federated/example-store/debug/metrics
registrations remain absent.

## Added reporting removal

The guarded Stage-18 replay applies the dedicated Mozc/Japanese reporting
excision after reconstructing the exact working density-resource baseline.
Japanese conversion, candidates, dictionaries, transliteration, rendering,
local learning, handwriting, GenAI, and the mixed Undo listener are mandatory
retained behavior.

The replay refuses an unexpectedly broad class deletion, scans all surviving
smali for references to deleted descriptors, rebuilds all four DEX files, and
runs the existing module-registry, `LatinApp.e()` Context-register, and exact
split-resource-ID gates.

## What remains intentionally absent

- `InAppJobService`
- `FeatureSplitDebugActivity`
- `FeatureSplitMultiprocessMetricsService`
- `SpeechPrecomputedFeatureExampleStoreService`
- `NWPSanityCheckEvalExampleStoreService`

These are federated/background-training example-store, debug, or metrics
surfaces—not required keyboard feature entry points.

## Native boundary

`libintegrated_shared_object.so` combines indispensable decoder/local-AI code
with metrics, training-cache, playlog, and Perfetto-named native code. Current
symbol, relocation, and direct-branch analysis does not prove all indirect
registration and function-pointer relationships. The branch therefore does not
zero, stub, or blindly delete native ranges. Doing so would violate the physical
removal standard and could silently destroy retained keyboard behavior.

The build remains a launchable removal checkpoint, not a privacy-certified
final release, until native code is safely separated or rebuilt and runtime
feature/network gates pass.

## Required runtime gate

1. Verify the installed APK SHA-256.
2. Render and type continuously.
3. Switch away and back.
4. Verify Japanese/Mozc conversion and local learning.
5. Verify local computation/personalization persistence.
6. Verify the explicit feedback screens.
7. Capture idle and ordinary-typing network behavior.
8. Capture each retained online feature only after deliberate invocation.
