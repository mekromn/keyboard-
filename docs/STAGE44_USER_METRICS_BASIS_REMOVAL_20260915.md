# Meboard Stage 44 — user-metrics permission / collection-basis removal

Status: **signed cumulative test candidate; static/build verification PASS; phone runtime pending; privacy-final NO**.

## Exact lineage

- Base: user-confirmed working **Stage 43 cumulative privacy + Moonshine**
- Stage-43 SHA-256: `378804d81aba41fd6daf6a37e94d88c6e6fedecb700b66f5ca2ecb036059a0d8`
- APK: `Meboard-stage44-USER-METRICS-BASIS-REMOVED-TEST.apk`
- Stage-44 SHA-256: `347127345444ba672e6335226984dddaf20262350b5c31cac347af18f17d14fe`
- Size: 110111139 bytes
- Package: `com.mekromn.meboard`
- Version code: `175940518`
- Version name: `18.0.3.954559732-release-arm64-v8a`
- Stable signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

Stage 44 is a direct descendant of Stage 43. No older APK is used as the build base.

## Physical removals

This pass removes the remaining direct bridge from the old **Share usage statistics** preference into `MetricsManager`, plus a closed orphan user-metrics collection-basis resolver cluster.

Deleted classes:

- `psa` — dynamic user-metrics preference `Supplier`; reads resource/key `0x7f140a2d` and installs the result into `MetricsManager`.
- `psp` — `UserMetricsPreferencesCollectionBasisResolver`.
- `mck` — `CollectionBasisResolverHolder` data holder for that resolver.
- `mcj` — `CollectionBasisResolverConditions` holder used only by the deleted holder.

Modified shared classes:

- `msp` — removes construction/installation of `psa`. The existing `MetricsManager` constructor's stock default supplier remains untouched; selector `0x13` returns `Boolean.FALSE`, so permission-gated user-reporting processors remain unapproved without retaining the deleted preference bridge.
- `fol` — removes the dead selector-16 callback that updated/logged `UserMetricsPreferencesCollectionBasisResolver`, and converts its switch table to a sparse table containing only the retained selectors.

No no-op replacement class is added.

## Closed-graph proof

Before mutation, typed descriptor ingress was bounded to:

- `Lpsa;`: only `psa` itself and `msp`.
- `Lpsp;`: only `psp`, its dead `fol` callback, and `mck`.
- `Lmck;`: only `mck` itself.
- `Lmcj;`: only `mcj` and `mck`.

The final signed decode contains none of `Lpsa;`, `Lpsp;`, `Lmck;`, or `Lmcj;`, and no `UserMetricsPreferencesCollectionBasisResolver`, `CollectionBasisResolverHolder`, or `CollectionBasisResolverConditions` marker remains.

## Cumulative regression containment

Stage 43 -> Stage 44 changes exactly **one non-signature APK payload**:

1. `classes.dex`

The payload entry set is unchanged. `classes2.dex`, `classes3.dex`, `classes4.dex`, `AndroidManifest.xml`, `resources.arsc`, both privacy/settings XML payloads, all assets and all native libraries are byte-identical to Stage 43.

Fresh decode comparison of the signed APK:

- main-DEX classes: **7465 -> 7461**
- deleted: exactly `mcj`, `mck`, `psa`, `psp`
- added: none
- changed surviving classes: exactly `fol`, `msp`

All six Meboard Moonshine/voice helper source files decode byte-for-byte identical to Stage 43, including the direct `org.futo.voiceinput.moonshine` target and deferred text-return machinery.

Locked Stage-28 cumulative removals remain preserved because Stage-43 `classes2.dex` and settings payloads are byte-identical:

- `Share usage statistics` absent
- `Improve for everyone` absent
- `Audio donations` absent
- `VoiceDonationManager` / `Lrqw;` absent
- `maybeAddDonationRequest` absent
- managed `enable_user_metrics` and `user_enable_federated_training` restrictions absent
- local `Personalize for you` and learned-data deletion controls retained

## Package/signing checks

- APK Signature Scheme v3: PASS
- v1/v2/v4 signing: disabled/not claimed
- stable Meboard signer: exact match
- ZIP integrity: PASS
- 16-KiB native-library alignment: PASS
- AAPT2 package/label parsing: PASS
- final signed Apktool 3.0.3 no-resource decode: PASS

## Runtime acceptance gate

Install directly over Stage 43 without clearing app data, then verify:

1. Keyboard opens and types normally.
2. Keyboard switching and ordinary settings still work.
3. Privacy screen still has none of the three removed sharing/donation rows.
4. Short microphone tap still launches normal Meboard dictation.
5. Long microphone press still launches Moonshine directly.
6. Moonshine's result is inserted back into the original field.

If this passes, Stage 44 becomes the next locked cumulative base. Remaining work still includes broader metrics/reporting infrastructure, residual Primes/diagnostics, Phenotype/experiment scaffolding, unresolved networking, and mixed native instrumentation; this stage is not privacy-final.
