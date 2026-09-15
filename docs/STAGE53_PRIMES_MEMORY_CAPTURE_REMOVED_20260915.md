# Meboard Stage 53 — orphaned Primes MemoryUsageCapture removal

Date: 2026-09-15. Status: **signed cumulative test APK; static/build verification PASS; phone runtime pending; privacy-final NO**.

## Artifact

- APK: `Meboard-stage53-PRIMES-MEMORY-CAPTURE-REMOVED-TEST.apk`
- SHA-256: `846fcb19ab9cd5fb7038280378d968bc19e417d81c269054e8dfd4571fde11dd`
- Size: 110078371 bytes
- Exact input / locked working base: Stage 52 (`6c3cad70f13fd229db0820991a5519bd4663277c45733a4604cdb3a89f13d739`)
- Package: `com.mekromn.meboard`
- Permanent signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

## Why this stage is safe

Stage 52 already removed the Primes memory metric service. In the Stage-52 signed APK, `uct` / `MemoryUsageCapture` has **zero constructor calls anywhere in all four DEX files**.

Its exact remaining typed-reference graph before this patch was:

- `uct` referenced only by shared synthetic providers `pdh`, `trn`, and its private helper `ucq`.
- `ucq` referenced only by `uct`.
- `pdh` selector 9 was constructed only by `uct.<clinit>`.
- the `trn` branch that directly type-cast to `uct` had no independent retained feature behavior; after deleting `uct`, that branch cannot receive a valid object of the deleted type.

Stage 53 therefore physically deletes:

- `uct` — Primes `MemoryUsageCapture` implementation
- `ucq` — its private provider/config-combiner helper

The `pdh` and `trn` branches that referenced the deleted class are replaced with explicit `UnsupportedOperationException` boundaries. No retained selector is redirected to another feature and no no-op telemetry implementation is added.

## Deliberate retained boundary

The separate `ucl` / `ucj` memory-state machinery, `uck` callback interface, `ucg` memory configuration, and shared `ucv` supplier remain. They have independent callers and are **not** classified as reporter-only by this stage.

## Signed-output proof

Relative to user-confirmed Stage 52:

- non-signature payload entry set: unchanged (9143 entries)
- changed payloads: exactly `classes.dex`
- `classes2.dex`, `classes3.dex`, `classes4.dex`: byte-identical
- `AndroidManifest.xml`: byte-identical
- `resources.arsc`: byte-identical
- cleaned privacy XMLs: byte-identical
- assets and all native libraries: byte-identical

Fresh decode of the actual signed Stage-53 APK versus signed Stage 52:

- Stage 52 main-DEX classes: **7453**
- Stage 53 main-DEX classes: **7451**
- deleted exactly: `uct`, `ucq`
- added: none
- changed surviving classes: exactly `pdh`, `trn`
- main DEX remains `dex 040`
- `MemoryUsageCapture.java` and the full Primes MemoryUsageCapture implementation marker are absent from all decoded DEX.

## Locked cumulative gates

PASS:

- Moonshine target `org.futo.voiceinput.moonshine` present.
- `VoiceProviderRelayActivity` and deferred text-return path present; custom Meboard helper smali unchanged.
- `Test Meboard` remains present.
- prior Stage-28/44 privacy removals remain absent.
- Stage-48 donation cluster remains absent.
- Stage-50 Primes network reporter remains absent.
- Stage-51 memory factory provider `ucu` remains absent.
- Stage-52 memory service graph `ucp/ucn/uco/uch/ucr/ucs` remains absent.
- APK Signature Scheme v3: PASS; v1/v2/v4 disabled.
- permanent Meboard signing certificate preserved.
- ZIP/native 16-KiB alignment: PASS.

## Runtime acceptance

Install directly over Stage 52 without clearing data and verify:

1. Normal typing.
2. Test Meboard opens/focuses.
3. Short mic tap uses normal Meboard dictation.
4. Long mic press launches Moonshine.
5. Moonshine text returns into the editor.
6. Background/foreground keyboard use remains stable.

If this passes, Stage 53 becomes the next locked cumulative base. The next memory-related target is the separate `ucl/ucj` memory-state machinery and remaining `ucg/ucv` configuration/supplier code, but only after classifying their independent callers so local stability behavior is preserved.
