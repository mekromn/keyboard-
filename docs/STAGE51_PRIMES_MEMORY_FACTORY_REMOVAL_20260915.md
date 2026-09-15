# Meboard Stage 51 — Primes memory reporter factory removal

Status: **signed cumulative test candidate; static/build verification PASS; phone runtime pending; privacy-final NO**.

## Exact artifact and lineage

- APK: `Meboard-stage51-PRIMES-MEMORY-FACTORY-REMOVED-TEST.apk`
- SHA-256: `229223d8a27ecdc5196079533a834cbe5d8ecebf5292ea407e8cdaf6e3c06ca5`
- Size: 110189488 bytes
- Package: `com.mekromn.meboard`
- Exact input: user-confirmed working Stage 50
- Stage-50 SHA-256: `86410921a48a31d8416c92f1016a2a8177bc69053b57c1613ef3754e66ea86ba`
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

Stage 51 descends directly from Stage 50. No older cleanup baseline is replayed.

## What this stage removes

The remaining Java Primes memory service is constructed only by the default branch of shared generated provider `uaz`.

On the exact signed Stage-50 decode:

- the entire APK contains exactly one typed `uaz` construction site;
- that site is in `eoi` and passes selector `1`;
- selector `1` enters `uaz`'s retained non-memory branch;
- the `ucp` Primes memory-service construction exists only in `uaz`'s default branch and therefore has no typed producer in the packaged application.

Stage 51 replaces that unreachable default branch with an explicit `UnsupportedOperationException` boundary rather than silently returning a no-op or another feature.

It also physically deletes `ucu`, a generated provider whose sole purpose is constructing `uct` (`MemoryUsageCapture`). A complete Stage-50 decoded-smali scan found `Lucu;` only in `ucu.smali` itself and no inbound typed reference.

The actual memory reporter/capture implementation (`ucp`, `uct`, `uco`, `ucn`, `ucq` and shared callback/config classes) remains packaged for the next stage. This stage intentionally removes the construction boundary first, mirroring the previously successful Stage-49 -> Stage-50 network reporter sequence.

## Signed-output preservation proof

Relative to Stage 50:

- non-signature payload entry set: identical (`9143` entries)
- changed payloads: exactly `classes.dex`
- unchanged payloads: `9142`
- `classes2.dex`, `classes3.dex`, `classes4.dex`: byte-identical
- AndroidManifest: byte-identical
- `resources.arsc`: byte-identical
- cleaned privacy XMLs: byte-identical
- assets and all native libraries: byte-identical

Fresh signed-output decode:

- main DEX: `7460 -> 7459`
- deleted: exactly `ucu`
- added: none
- changed surviving class: exactly `uaz`
- DEX version remains `040`

## Locked cumulative gates

PASS:

- Moonshine target `org.futo.voiceinput.moonshine` remains present.
- `VoiceProviderRelayActivity`, `VoiceProviderChooser`, `VoiceProviderActionRunnable`, `VoiceResultCommitRunnable`, plus the existing `mhe`, `mln`, and `unb` microphone integration smali are byte-for-byte identical to Stage 50.
- `Test Meboard` remains present.
- prior `VoiceDonationManager` / `rqw` removal remains intact.
- `psa`, `psp`, `mck`, `mcj` user-metrics/collection-basis removals remain intact.
- Stage-48 donation cluster remains absent.
- Stage-50 Primes network reporter (`uda`, `ucy`) remains absent.
- APK Signature Scheme v3: PASS; v1/v2/v4 disabled.
- permanent Meboard signing certificate preserved.
- ZIP/native 16-KiB alignment: PASS.

## Runtime acceptance gate

Install directly over Stage 50 without clearing data and verify:

1. Normal typing.
2. `Test Meboard` opens and focuses its field.
3. Short microphone tap launches normal Meboard dictation.
4. Long microphone press launches Moonshine directly.
5. Moonshine output is committed back into the editor.
6. Normal online keyboard features you use continue working.
7. No crash during ordinary app/keyboard background/foreground transitions.

If this passes, Stage 51 becomes the locked cumulative base. The next safe cut is the now-unconstructible Java Primes memory reporter/capture implementation itself, with shared callback branches reviewed individually rather than deleting generic Android memory/stability helpers.

## Remaining cleanup

Privacy cleanup is not final. Remaining areas include the Primes memory implementation after this factory gate, Primes jank/frame/Perfetto instrumentation, residual diagnostics and Phenotype scaffolding, mixed local-computation/training configuration requiring consumer proof, dead resource-table strings, native reporting/instrumentation, and the final whole-app outbound-network/regression audit.
