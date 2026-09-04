# Physical privacy-removal policy

Meboard accepts only **physical removal** for code and data paths that fall inside the privacy-removal scope. It does **not** classify every local measurement, counter, timer, or diagnostic value as removable telemetry merely because it has a metrics-related name.

## Exact removal scope

Physically remove both of the following categories wherever they are technically separable from retained keyboard behavior:

1. **Outbound reporting telemetry** — collection, enrichment, serialization, persistence, scheduling, retry, transport, or upload logic whose purpose includes sending analytics, usage, diagnostics, performance data, experiments, attribution, training examples, gradients, checkpoints, learned personalization, model state, or derived model updates off-device.
2. **Nonessential local instrumentation** — local-only metrics, traces, event histories, counters, debug logging, caches, or collectors that have no demonstrated consumer required by a retained keyboard feature, stability mechanism, recovery path, local AI/personalization path, or quality-control algorithm.

The following may remain only when dependency and data-flow analysis demonstrates that a retained feature actually consumes them and that they have no reachable outbound reporting sink:

- local state needed by candidate generation, ranking, autocorrection, decoding, handwriting, dictation, personalization, or other retained keyboard behavior;
- local counters/timers needed for adaptive feature behavior, resource management, scheduling, cache eviction, or quality decisions;
- crash-recovery and corruption-recovery state required to keep the keyboard usable;
- strictly local diagnostics required by a retained feature to function correctly;
- user-visible local history or statistics deliberately exposed as a feature.

A metrics-looking name is therefore not sufficient evidence for deletion. Conversely, storing a value locally first does not make it acceptable when that value ultimately feeds an uploader, reporting processor, remote experiment system, or federated-training result path.

## Definition of removed

A targeted subsystem is considered removed only when its executable implementation, registration, scheduling, persistence, serialization, transport, and associated resources are absent from the rebuilt package wherever separable from retained functionality.

For a dedicated reporting subsystem, this normally means deleting its classes/packages/components/resources outright. For reporting mixed into shared keyboard code, remove the reporting-specific members and control-flow branches, then recursively delete dependencies made dead by that removal.

For retained local instrumentation, document:

- the retained feature or stability path that consumes it;
- the call/data-flow evidence for that dependency;
- the absence of a reachable upload/reporting sink;
- why removing it would degrade or break retained behavior.

## Explicitly forbidden substitutes

None of these count as removal:

- setting a feature flag or preference to false;
- replacing targeted methods with no-op bodies;
- adding an early return;
- keeping an empty service/receiver/provider shell;
- leaving dead or unreachable targeted classes in DEX;
- leaving separable targeted native implementation in a shipped `.so` but never calling it;
- blocking DNS/hosts/firewall/network-security configuration;
- corrupting or replacing reporting URLs/endpoints;
- removing only manifest registrations while implementation remains;
- relying on server-side rejection, signed-out state, or missing credentials;
- renaming or obfuscating targeted symbols.

## Required removal targets

Remove, where present and not required by a deliberately retained user-facing feature:

- Clearcut logging, buffering, event enrichment, and upload infrastructure;
- Primes analytics/performance/network reporting and upload paths;
- federated learning and Brella participation;
- background training eligibility, example harvesting, scheduling, caches, result handling, and transport;
- any upload of local AI state, learned personalization, training examples, gradients, checkpoints, or derived model updates;
- remote experiment/Phenotype fetch, update, receiver, storage, and selection machinery that is not required to provide deterministic local feature defaults;
- automatic crash/ANR/jank/memory/battery/network diagnostic reporting;
- reporting-only trace/Perfetto triggering;
- analytics processors whose purpose is recording or reporting usage behavior;
- account discovery, account classification, account-derived personalization seeding, account listeners, account tokens, and account identity attached to feedback or feature traffic;
- attribution and campaign reporting such as RLZ;
- reporting-only jobs, services, receivers, providers, workers, alarms, callbacks, startup registrations, databases, preferences, caches, protobufs, queues, retry/backoff, and upload state;
- telemetry-only feature splits and telemetry-only native libraries;
- unnecessary background network clients and endpoints;
- local debug/performance instrumentation with no retained functional consumer.

## Retained networking

Networking may remain only for deliberately retained user-facing features, including:

- explicit language/model downloads;
- active voice dictation;
- user-invoked GIF, sticker, translation, or other online content lookup;
- explicit anonymous help/feedback submission;
- another feature specifically retained by the project owner.

Retained online behavior must be user-triggered whenever the feature permits, operate signed-out/anonymous wherever possible, never discover or broadcast the device's Google account, and never upload local model or learned-personalization data.

Retention of a feature does not exempt passive reporting attached to it. Analytics, diagnostics, experiment reporting, attribution, and background usage reporting must still be removed from the feature's transport path. Explicit feedback may send only the content the user deliberately submits plus the minimum technical context genuinely required for that requested report; account identity and automatic unrelated diagnostics are excluded.

## Native code rule

If a shipped native library contains separable outbound reporting or nonessential local instrumentation, that implementation must be removed from the native binary or the library must be rebuilt/omitted. Merely deleting Java/JNI call sites is insufficient when the targeted implementation remains packaged.

Do not delete native code solely because a symbol or string contains `metric`, `trace`, `stats`, or a similar term. Establish function boundaries, registration, callers, consumers, relocations, and reachable sinks first. Native local instrumentation required by the decoder, local AI, recovery, or retained feature behavior may remain only with the retention evidence described above.

If an indispensable native library combines retained functionality and targeted implementation that cannot yet be separated safely, that is a blocker to claiming completion. Document the blocker rather than labeling the build privacy-certified.

## Classification procedure

Each ambiguous surface must be classified using trigger, consumer, and sink evidence:

| Classification | Trigger/consumer/sink | Treatment |
|---|---|---|
| Outbound reporting | Automatic or background collection with a reachable serialization/transport/upload sink | Physically remove |
| Feature-attached reporting | Retained feature works without the analytics/diagnostic branch | Remove reporting branch; retain feature |
| User-requested network feature | Network starts because the user invokes the retained feature | Retain minimally, anonymous/signed-out |
| Essential local instrumentation | A retained feature, local AI path, stability mechanism, or recovery algorithm consumes it; no reachable egress | Retain and document |
| Unused local instrumentation | No retained functional consumer and no user-visible purpose | Physically remove |
| Unknown | Trigger, consumer, or sink has not been established | Do not delete blindly; do not certify release |

## Verification gates

A release may be called privacy-certified only after all of these pass:

1. Decoded DEX/smali/source inspection finds no targeted implementation classes or reporting branches.
2. Manifest inspection finds no targeted reporting components, permissions, or metadata.
3. Resource inspection finds no configuration/resources used only by removed subsystems.
4. Native analysis finds no targeted implementation in shipped libraries, except reviewed retained local code with documented functional evidence.
5. Static call/data-flow inspection shows no remaining path from telemetry sources to network/reporting sinks.
6. Account isolation checks find no account discovery, listeners, classification, token acquisition, account-derived personalization seeding, or account identity propagation.
7. Model-privacy checks find no path capable of uploading local model state, examples, gradients, checkpoints, learned data, or derived updates.
8. Removed feature splits are absent from the delivered package; retained splits contain no passive reporting path.
9. Idle startup and ordinary offline typing produce no unsolicited network activity.
10. Retained network traffic occurs only when its user-facing feature is invoked or a user-requested download is running.
11. Retained local instrumentation has a recorded functional consumer and no reachable egress.
12. Before/after class, method, file, and package-size deltas demonstrate actual code excision.
13. The physical-removal and privacy verifiers pass against the decoded/rebuilt output, with every exception explicitly reviewed and documented.
14. `LatinIME` binds, renders, types, and survives switching away and back without relying on removed reporting infrastructure.

## Claiming status

Until every applicable gate passes, use wording such as **"removal in progress"**, **"launchable checkpoint"**, or **"telemetry paths identified"**. Do not call a build telemetry-free or privacy-certified merely because reporting is disabled, blocked, unreachable by configuration, or currently unauthenticated.
