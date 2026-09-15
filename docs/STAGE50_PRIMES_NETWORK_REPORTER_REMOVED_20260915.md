# Meboard Stage 50 — Primes network reporter implementation removal

Status: signed cumulative test candidate; static/build verification PASS; phone runtime pending; privacy-final NO.

## Artifact
- APK: `Meboard-stage50-PRIMES-NETWORK-REPORTER-REMOVED-TEST.apk`
- SHA-256: `86410921a48a31d8416c92f1016a2a8177bc69053b57c1613ef3754e66ea86ba`
- Exact input: user-confirmed Stage 49, SHA-256 `b65613b116dc017e3bc8054992089ebffe4544149e9c93cec085c302ad2628ed`
- Package/signing identity unchanged; permanent signer certificate SHA-256 `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`.

## Physical removal
Stage 49 removed the only typed construction path for the Primes network reporter. Stage 50 deletes the now-unconstructible implementation and dedicated converter:
- `uda` — `NetworkMetricServiceImpl`
- `ucy` — dedicated network-event to network-metric converter

Shared callback classes are retained with only their dead network-reporting branches removed:
- `rup`: dedicated `Luda` constructor overload and selector-7/default network capture/report block removed.
- `iju`: selector 19, produced only by `Luda`, replaced with an explicit removed-branch rejection.
- `tfh`: network-reporter default/retry branch removed; retained typed callers use selectors 0 and 1.

Actual keyboard transports, request paths, downloads/GIF networking, voice providers, and user-triggered networking are not removed.

## Closed graph proof
On the exact signed Stage-49 decode, every `Luda;` reference was confined to `uda`, `rup`, `iju`, `tfh`; every `Lucy;` reference was confined to `ucy`, `uda`, `rup`, `iju`. The dedicated `rup(Luda, Lucx, Luen, int)` overload had exactly one caller in `uda`. `iju` selector 19 had no producer outside `uda`.

## Signed-output boundary
Stage 49 -> 50 changes exactly two APK payloads: `classes2.dex` and `classes3.dex`.
- `classes.dex`: byte-identical
- `classes4.dex`: byte-identical
- manifest/resources/privacy XML/assets/native libraries: byte-identical

Fresh signed decode:
- main DEX: 7460 -> 7460, zero changes
- classes2: 9504 -> 9504, exactly `iju`, `rup`, `tfh` changed
- classes3: 4145 -> 4143, exactly `uda`, `ucy` deleted; no surviving class changed
- classes4: 630 -> 630, zero changes
- no `Luda;`, `Lucy;`, `NetworkMetricServiceImpl`, or `NetworkCapture.java` marker remains

## Locked cumulative gates
- Moonshine target `org.futo.voiceinput.moonshine` preserved.
- `VoiceProviderRelayActivity`, `VoiceProviderChooser`, and `VoiceProviderActionRunnable` are byte-for-byte identical to Stage 49.
- `Test Meboard` preserved.
- prior voice-donation, user-metrics/collection-basis, and earlier privacy removals remain absent.
- signed APK passes v3 signature verification and 16-KiB alignment.

## Runtime gate
Install directly over Stage 49 without clearing data. Verify normal typing, Test Meboard, short-tap standard dictation, long-press Moonshine with returned text, and normal online keyboard features such as GIF/download paths.

Privacy cleanup is not final. Remaining work includes separable Primes memory/jank reporters, residual diagnostics/Perfetto/Phenotype scaffolding, mixed local-computation/training configuration requiring consumer proof, native reporting/instrumentation, and the final whole-app outbound-network audit/regression sweep.
