# Meboard Stage 52 — Primes memory service implementation removal

Date: 2026-09-15. Status: **signed cumulative test APK; static/build verification PASS; phone runtime pending; privacy-final NO**.

## Artifact

- APK: `Meboard-stage52-PRIMES-MEMORY-SERVICE-REMOVED-TEST.apk`
- SHA-256: `6c3cad70f13fd229db0820991a5519bd4663277c45733a4604cdb3a89f13d739`
- Size: 110189488 bytes
- Exact input / locked working base: Stage 51 (`229223d8a27ecdc5196079533a834cbe5d8ecebf5292ea407e8cdaf6e3c06ca5`)
- Package: `com.mekromn.meboard`
- Permanent signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

## Why this stage is safe

Stage 51 removed the only typed construction branch for the Primes memory metric service. In Stage 52, the remaining service graph is closed: the service and its helpers reference only each other plus one memory-only branch in shared async helper `uqx`.

The deleted classes are:

- `ucp` — `MemoryMetricServiceImpl` service implementation
- `ucn` — service callback
- `uco` — memory-capture/result continuation
- `uch` — private service state object
- `ucr`, `ucs` — data helpers used only by that continuation

The only surviving class changed is `uqx`; its `ucp` constructor and memory-service branch are removed while its unrelated `Luqy` asynchronous-list branch is preserved.

## Deliberate retained boundary

`uct` / `MemoryUsageCapture`, `ucg` memory configuration and related shared utilities remain. They still have surviving callers outside the deleted service graph, including non-service memory utilities, so they are not classified as reporter-only yet. This stage does not remove Android memory-pressure/stability behavior.

## Signed-output proof

Relative to user-confirmed Stage 51:

- non-signature payload entry set: unchanged (`9143` entries)
- changed payloads: exactly `classes.dex`
- `classes2.dex`, `classes3.dex`, `classes4.dex`: byte-identical
- AndroidManifest.xml: byte-identical
- `resources.arsc`: byte-identical
- privacy XMLs, assets and all native libraries: byte-identical

Fresh signed-APK decode:

- Stage 51 main-DEX classes: `7459`
- Stage 52 main-DEX classes: `7453`
- deleted exactly: `uch`, `ucn`, `uco`, `ucp`, `ucr`, `ucs`
- added: none
- changed surviving class: exactly `uqx`
- main DEX remains `dex 040`

## Locked cumulative gates

PASS:

- Moonshine target `org.futo.voiceinput.moonshine` present.
- `VoiceProviderRelayActivity` and deferred text-return path present.
- `Test Meboard` present.
- prior Stage 28/44 privacy removals remain absent.
- Stage 48 donation cluster remains absent.
- Stage 50 Primes network reporter remains absent.
- Stage 51 `ucu` remains absent.
- APK Signature Scheme v3: PASS; v1/v2/v4 disabled.
- permanent Meboard signing certificate preserved.
- ZIP/native 16-KiB alignment: PASS.

## Runtime acceptance

Install directly over Stage 51 without clearing data and verify:

1. Normal typing.
2. Test Meboard opens/focuses.
3. Short mic tap uses normal Meboard dictation.
4. Long mic press launches Moonshine.
5. Moonshine text returns into the editor.
6. Background/foreground keyboard use remains stable.

If this passes, Stage 52 becomes the next locked cumulative base. The next memory-cleanup target is the remaining shared `MemoryUsageCapture`/configuration utilities, but only after classifying their non-service callers so local memory-pressure/stability behavior is not removed accidentally.
