# Physical telemetry removal policy

This project accepts only **physical removal of telemetry implementation code**.

## Definition of removed

A telemetry subsystem is considered removed only when its executable implementation, registration, scheduling, persistence, serialization, transport, and associated resources are absent from the rebuilt application package wherever they are technically separable from retained functionality.

For a dedicated telemetry subsystem, this normally means deleting its classes/packages/components/resources outright. For telemetry mixed into shared keyboard code, remove the telemetry-specific members and control-flow branches, then recursively delete now-unused telemetry dependencies.

## Explicitly forbidden substitutes

None of these count as removal:

- setting a feature flag or preference to false;
- replacing telemetry methods with no-op bodies;
- adding an early return;
- keeping an empty service/receiver/provider shell;
- leaving dead or unreachable telemetry classes in DEX;
- leaving native telemetry implementation in a shipped `.so` but never calling it;
- blocking DNS/hosts/firewall/network security config;
- corrupting or replacing telemetry URLs/endpoints;
- removing only manifest registrations while implementation remains;
- relying on server-side rejection or missing credentials;
- renaming or obfuscating telemetry symbols.

## Required removal scope

The removal pass must include, where present:

- Clearcut logging and upload infrastructure;
- Primes telemetry/performance/network reporting;
- federated learning and Brella integration;
- background training eligibility, scheduling, caches, result handling, and transport;
- remote experiment/Phenotype fetch, update, receiver, storage, and selection machinery that is not required locally;
- telemetry-specific crash/diagnostic collection and upload;
- telemetry-specific trace/Perfetto triggering;
- analytics/metrics processors whose purpose is recording or reporting usage telemetry;
- survey/feedback upload code not deliberately retained as a user-requested feature;
- telemetry-specific jobs, services, receivers, providers, workers, alarms, callbacks, and startup registration;
- telemetry-specific databases, preferences, caches, protobufs/serializers, queueing, retry/backoff, and upload state;
- telemetry-only feature splits and telemetry-only native libraries;
- unnecessary background network clients and endpoints.

## Retained networking

Networking may remain only for deliberately retained user-facing features, such as:

- explicit language/model downloads;
- active voice dictation;
- explicit GIF/sticker/online content lookup;
- another feature specifically chosen by the project owner.

Retention of a feature does not exempt telemetry attached to that feature. Analytics, diagnostics, experiment reporting, and background usage reporting must still be removed from its path.

## Native code rule

If a shipped native library contains a separable telemetry implementation, that implementation must be removed from the native binary or the library must be rebuilt/omitted. Merely deleting Java/JNI call sites is insufficient if the telemetry implementation remains packaged.

If the native library combines indispensable retained functionality and inseparable telemetry code, that is a blocker to claiming complete physical removal. The repository must document the blocker instead of labeling the build telemetry-free.

## Verification gates

A release may be called telemetry-removed only after all of these pass:

1. Decoded DEX/smali/source inspection finds no targeted implementation classes or telemetry branches.
2. Manifest inspection finds no targeted telemetry component registrations or metadata.
3. Resource inspection finds no telemetry-specific configuration/resources required only by removed subsystems.
4. Native binary inspection finds no targeted telemetry implementation markers in shipped native libraries, aside from reviewed non-executable residue with a documented justification.
5. Static call/reference search shows no remaining references to removed telemetry packages/classes/methods.
6. Removed feature splits are absent from the delivered bundle.
7. Runtime idle and ordinary typing tests show no unsolicited network activity.
8. Retained networking occurs only as a result of the retained user-facing feature being invoked or a user-requested download.
9. Before/after class, method, file, and package-size deltas are recorded to demonstrate actual code excision.
10. `tools/verify_physical_removal.py` passes against the decoded/rebuilt output, with any exception explicitly reviewed and documented.

## Claiming status

Until these gates pass, use wording such as **"removal in progress"** or **"telemetry paths identified"**. Do not call a build telemetry-free merely because telemetry is disabled or network-blocked.
