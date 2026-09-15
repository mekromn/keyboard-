# Meboard Stage 49 — Primes network-metric factory path removal

Status: **signed cumulative test candidate; static/build verification PASS; device runtime pending; privacy-final NO**.

## Artifact

- APK: `Meboard-stage49-PRIMES-NETWORK-FACTORY-REMOVED-TEST.apk`
- SHA-256: `b65613b116dc017e3bc8054992089ebffe4544149e9c93cec085c302ad2628ed`
- Size: `110189488` bytes
- Package: `com.mekromn.meboard`
- Base: exact user-confirmed Stage 48 APK, SHA-256 `026b7a1961d515e37a38ae609ac4dc2be00c46d44cea0a4fa9179fe6e0c5497f`
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

## What this stage removes

Stage 48 still packaged the Primes network-metric service construction in the default branch of shared provider `tzq`, even though the exact current APK has only one typed `tzq` constructor site and it is fixed to selector `1` using the `[B]` constructor overload. The network/default selector has no typed producer in this build.

Stage 49 therefore:

1. Removes the unreachable `tzq` default branch that constructed `Luda` / `NetworkMetricServiceImpl`.
2. Replaces that impossible selector with an explicit `UnsupportedOperationException` boundary instead of constructing another feature or silently returning a no-op.
3. Physically deletes `twk`, an entirely unreferenced Primes core-metric provider class. A complete main-DEX reference scan found zero inbound `Ltwk;` references before deletion.

This stage does **not** yet delete the still-packaged `Luda` network reporter implementation and its callback/collector helpers. Those remain the next cleanup target after this runtime gate, because Stage 49 first removes their only construction path.

## Signed-output preservation proof

Relative to the user-confirmed Stage 48 APK:

- Non-signature payload entries: `9143`
- Changed payloads: exactly `classes.dex`
- Unchanged payloads: `9142`
- `classes2.dex`, `classes3.dex`, `classes4.dex`: byte-identical
- AndroidManifest: byte-identical
- `resources.arsc`: byte-identical
- cleaned privacy XMLs: byte-identical
- assets and all native libraries: byte-identical

Fresh decode of the signed Stage-49 APK versus signed Stage 48 main DEX:

- Stage 48 main-DEX classes: `7461`
- Stage 49 main-DEX classes: `7460`
- deleted: exactly `Ltwk;`
- added: none
- changed surviving class: exactly `Ltzq;`

The main DEX remains `dex 040`.

## Locked cumulative gates

PASS:

- Moonshine package target `org.futo.voiceinput.moonshine` remains present.
- Moonshine relay/chooser/deferred-result helper smali checked byte-for-byte identical to Stage 48.
- `Test Meboard` remains present in `classes2.dex`.
- previously removed `VoiceDonationManager` / `rqw` path remains absent.
- previously removed `psa`, `psp`, `mck`, `mcj` user-metrics/collection-basis classes remain absent.
- Stage-48 donation cluster remains absent.
- ZIP/native 16-KiB alignment: PASS.
- APK Signature Scheme v3: PASS; v1/v2/v4 disabled.
- permanent Meboard signing certificate preserved.

## Runtime acceptance gate

Install directly over Stage 48 without clearing data and verify:

1. Normal typing.
2. `Test Meboard` opens and focuses its test field.
3. Short mic tap launches normal Meboard dictation.
4. Long mic press launches Moonshine directly.
5. Moonshine result is inserted back into the editor.
6. Normal online keyboard features you use (for example GIF/download paths) still behave normally.

If this passes, Stage 49 becomes the next locked cumulative base. The next safe removal is the now-unconstructible Primes network reporter implementation/callback cluster itself, not any retained keyboard transport.
