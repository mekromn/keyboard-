# Meboard Stage 20 — trainer configuration residue removal

Date: 2026-09-12. Status: **signed test APK; static/build verification PASS; device runtime pending; privacy-final NO**.

## Exact artifact and working recovery point

- New APK: `Meboard-stage20-Federated-config-removed-TEST.apk`
- APK SHA-256: `05f16f7e94c17426a988961e15856059ba82b30a30e4dd992ae1d14a757fc7e3`
- Size: 110132140 bytes
- Package: `com.mekromn.meboard`
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`
- APK Signature Scheme v3: verified. No v2 verification claim is made.
- Immediate working rollback: `Meboard-stage19-BaseClearcut-removed-TEST.apk`
- Stage-19 SHA-256: `c06c75a38f61baf442f0ed040d03dcd41cec1c45a528184ae7ca4d3be77611d4`
- Stage-19 user report on 2026-09-12 at 17:43:44 UTC: "Works. Continue".
- Preserved working branch: `meboard/working-stage19-20260912`, checkpoint commit `5c7e128bd1c517fae440bbb4c62b7c1a58f51528`.
- Stage-20 implementation commit: `4e0832e676747e3038e00c2a55143d9c14a5a803`.
- Stage-20 test branch: `meboard/stage20-trainer-config-test-20260912`.

The user report confirms general Stage-19 operation, not an exhaustive feature sweep or network audit. The installed device APK was not re-read. The Stage-19 binary in the build environment was re-hashed. Earlier Stage-16 recovery artifacts and branches remain unchanged.

## Physical removal, not disabling

Three unused configuration chains were removed end-to-end:

| Removed setting | Flag accessor | Consumer-facing accessor | Supplier branch |
|---|---|---|---|
| `TrainerFeature__http_federated_compute_protocol_base_uri` and its federated-compute endpoint literal | `aamv.ad()` / `aams.ad()` | `lhk.Z()` / `lgp.Z()` | `lhi`, selector 6 |
| `TrainerFeature__droid_guard_reduced_configuration_flow_name` | `aamv.Z()` / `aams.Z()` | `lhk.X()` / `lgp.X()` | `lhi`, selector 11 |
| `TrainerFeature__droid_guard_enabled` | `aamv.ar()` / `aams.ar()` | `lhk.aJ()` / `lgp.aJ()` | `lhg`, selector 20 |

This deletes **12 method definitions/declarations and three supplier branches across six existing classes**. No classes or no-op replacements were added. No entire mixed configuration class was deleted. Class count remains 21762; **21756 class files are entirely unchanged**. Net decoded-smali reduction: 5270 bytes. APK byte size remains unchanged because packaging/alignment can absorb small code-size changes.

All consumer-facing accessors above had no typed Java caller in Stage 19. The deleted lower accessors were reached only by the reviewed supplier branches; each removed selector had exactly one producer in the removed wrapper. The patch checks these conditions again before writing and rejects target-file drift. Exact short class tokens for the relevant interfaces/implementations and the endpoint were not found in the packaged native libraries. These are static checks, not a universal proof against every possible dynamic lookup.

The two middle `lhi` cases are removed using a sparse switch. For `lhg`, the unused selector-20 default body is deleted and the original selector-19 body becomes the natural default. All 39 retained numeric selector results were independently compared and are unchanged.

This is dead-code removal, **not evidence that the deleted endpoint was previously transmitting**, and **not a claim that all DroidGuard or all federated-related code is gone**.

## Preservation and artifact verification

| Check | Result |
|---|---|
| Exact Stage-19 input hash and six decoded target hashes | PASS |
| Independent retained-method comparison within changed classes | 447 methods byte-identical |
| Independent retained supplier dispatch comparison | 39 numeric selector cases unchanged |
| References to removed method descriptors | None in surviving smali |
| All-payload scan for endpoint and all three flag names | All absent |
| Existing module-registry register checks | PASS |
| Existing Mozc / Undo / local-computation / anonymous-feedback static gate | PASS |
| Current privacy-policy static gate | PASS, zero fatal findings under that gate |
| DEX assembly and header/SHA-1/Adler32 checks | PASS |
| ZIP CRC integrity | PASS |
| Original signing certificate / APK v3 signature | Verified |
| 16 KiB ZIP alignment | PASS |
| Independent clean replay from pinned Stage 19 | All payload entries identical |
| Device runtime and network capture | NOT RUN |

Only `classes.dex` and `classes2.dex` changed. The other **9146 of 9148 non-signature payload entries are byte-identical** to Stage 19. This includes the manifest, resources, assets, DEX files 3 and 4, and all 16 native libraries. Local-learning/local-computation defaults and retained methods were not changed. No native decoder/AI code was modified.

Fresh static network inventory: background/reporting candidates **1 -> 0**, user-feature candidates **50**, unresolved **386**. That classifier relies on names, literals and API references; zero candidates in its named bucket does not prove zero telemetry. Existing review-only inventory still includes federated/training (200-result cap), MetricsProcessor (3), Perfetto (22), Primes (87), and Phenotype (108) matches.

## Replay proof

Two clean Stage-20 transformations/builds from the pinned Stage-19 APK reproduced the exact same 9148 payload entries. The first assembly was resumed after an execution timeout; the second driver completed end-to-end successfully.

Unsigned clean-replay SHA-256: `8478690bd481c64bfaebc6369e03231185de7a21fa8c408397c13612fff44018`.

- `classes.dex`: `cb03267b7f30126d3780021adf366e441a56222c84b4acfc68f54f64e6230454`
- `classes2.dex`: `86407002a3d48a7c3c3d921f4f4c5a579c75bf9ffaf660b1551a9481450b69d7`

This is a replay from the pinned Stage-19 binary, not a new full replay from pristine Gboard. The three new GitHub script blobs were checked against the actual tested local files and match exactly. The existing `MeboardSmaliAssembler.java` is reused unchanged.

```sh
python tools/build_stage20_test.py \
  --input /path/to/Meboard-stage19-BaseClearcut-removed-TEST.apk \
  --apktool /path/to/apktool-3.0.3.jar \
  --work /path/to/new-empty-work-directory \
  --output /path/to/stage20-unsigned.apk
```

The driver pins Apktool SHA-256 `dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423`. Same-key signing options are `--build-tools`, `--keystore`, `--alias`, and `--password-env`. Private signing material and APKs are not in GitHub.

## Acceptance and next removal

Install the signed Stage-20 test over same-signer Stage 19 without clearing app data. Keep the exact Stage-19 rollback. Check normal typing, switching away/back, learned-word persistence, Undo, Japanese conversion, voice, clipboard, and usual online features. Stage 20 is not promoted to working until the user reports its result.

Next targets require branch-level review: the federated versus local scheduling paths in `lnk.m(JIZ)J`, and reporting/federated-specific fields passed through the mixed native-configuration builder `sal.h`. Some federated-named settings still have shared consumers, so they were deliberately not deleted by name. Residual Primes, experiment/diagnostic code, unresolved networking, and native reporting remain separate work.
