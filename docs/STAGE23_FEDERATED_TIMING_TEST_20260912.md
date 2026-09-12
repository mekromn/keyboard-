# Meboard Stage 23 — federated timing/configuration removal

Date: 2026-09-12. Status: **signed test APK; static/build checks PASS; phone runtime pending; privacy-final NO**.

## Exact artifact and provenance

| Item | Value |
|---|---|
| New APK | `Meboard-stage23-Federated-timing-removed-TEST.apk` |
| SHA-256 | `08073c39f009b7679c36fa1a4364d42fe945b755ac66062627da85a65351d401` |
| Size | 110132140 bytes |
| Package | `com.mekromn.meboard` |
| Signer certificate SHA-256 | `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15` |
| Exact build input | `Meboard-stage22-Initial-federated-scheduling-removed-TEST.apk` |
| Stage-22 SHA-256 | `8cf20fabd5ccba93aae7187fa27f4ffe3cbb3bed37a42c73d1e7c34c65db4766` |
| Input source/report commit | `dbe73b8fc02b744b5ff960fa5a2442c1e03f4127` |
| New test branch | `meboard/stage23-federated-timing-test-20260912` |
| Complete tested-tooling commit | `a418fad87f5504583055bd65c649dfe087ade6f2` |

The Stage-22 input and delivered Stage-23 output were independently re-hashed. No APK was read back from the phone. The user reported the intermittent voice issue no longer reproducible, then authorized continuation. They did not identify whether they had installed the suggested Stage-21 rollback, so the current phone build is not assumed. Stage 22 is the exact code base of this test, not a newly certified working/voice checkpoint. All existing rollback APKs and working branches remain unchanged.

## Physical removal

The shared timing helpers are now specialized to the retained local-computation path:

- `lnk.m(JIZ)J` becomes `lnk.m(J)J`: delete the federated scheduling calculations and remove the unused job-type/local-versus-federated arguments.
- `lnk.h(JJLlgw;Z)Lzvi;` becomes `lnk.h(JJLlgw;)Lzvi;`: remove the obsolete mode parameter and migrate its call to the reduced timing helper.
- Migrate the four external calls in `lna` and `lnc` and the one internal helper call. An independent forward control-flow check confirms all reviewed external calls supplied local mode, including exceptional edges.

Three configuration chains exclusively consumed by the removed federated path are physically deleted:

1. `TrainerFeature__inapp_training_max_scheduling_period_secs`.
2. `TrainerFeature__min_user_specified_scheduling_interval_sec_for_federated_computation`.
3. `TrainerFeature__max_user_specified_scheduling_interval_sec_for_federated_computation`.

This removes **12 configuration method definitions/declarations and three supplier branches**. The deleted supplier selectors are `lhh:6,10` and `lhf:12`; their tables become sparse switches, with the remaining selectors preserved. No classes or no-op replacements were added. The local configuration accessors and their defaults remain unchanged.

Exactly **nine class files changed**: `aams`, `aamv`, `lgp`, `lhk`, `lnk`, `lhf`, `lhh`, `lna`, and `lnc`. Class count remains **21761**; **21752 complete class files are unchanged**. Net decoded-smali reduction is **7325 bytes**. The packaged APK size stayed the same after alignment; no APK-size saving is claimed.

## Preservation details

The retained timing calculation still uses the original local minimum/maximum settings, seconds-to-milliseconds conversion, clamp order, and getter order. The deadline helper preserves timestamp arguments and 64-bit addition behavior.

The removed parameter register was also the upper half of a temporary wide value in the old deadline helper. The patch explicitly moves that temporary into the already-consumed `v4/v5` pair rather than leaving an out-of-range parameter or corrupting another argument. The tests model physical register indices, parameter/local aliases, and both halves of long values.

Surrounding caller instructions, constants, exception regions, and cancellation/completion behavior are unchanged apart from the reduced argument handoff. The public initial-registration and completion-dispatch entry points from prior stages are not changed by this pass.

## Verification results

| Check | Result |
|---|---|
| Exact input APK and nine guarded decoded-file hashes | PASS |
| External caller mode analysis | All four reviewed calls proven local |
| Local clamp comparisons, including signed/saturation boundaries | 9600 cases matched |
| Deadline/register comparisons, including signed overflow boundaries | 4096 cases matched |
| Deliberately wrong local getter mutation | Detected by the test |
| Retained configuration-provider selector cases | 39 unchanged |
| Other surviving methods in the nine changed classes | 458 byte-identical |
| Compiled DEX references to the 12 deleted accessors and two old signatures | All absent |
| New timing signatures in compiled DEX method indexes | Present |
| All three removed flag names across every packaged payload | Absent |
| Class-definition sets in all four DEX files | Unchanged |
| Existing module-registry register gate | PASS |
| Existing Mozc / Undo / local-computation / anonymous-feedback gate | PASS |
| Current privacy-policy static gate | PASS; zero known fatal findings under that gate |
| DEX assembly, headers, SHA-1 and Adler32 checks | PASS |
| ZIP CRC integrity | PASS |
| Original signing certificate / APK Signature Scheme v3 | Verified |
| 16 KiB ZIP alignment | PASS |
| Independent first-build versus clean signed rebuild | All 9148 payload entries identical |
| Phone runtime / voice test / network capture | NOT RUN |
| Privacy-final | NO |

The arithmetic and register checks are bounded static/interpreter tests, **not Android runtime tests**. External enum and timestamp functions are modelled; the comparison proves that the reviewed code supplies the same calls/arguments in the tested local cases, not that all external behavior has been executed. The signature verifier reports v3 verified and v2 not verified; no v2 verification claim is made.

Only **`classes.dex` and `classes2.dex` changed**. The other **9146 of 9148 non-signature payload entries are byte-identical** to Stage 22, including the manifest, keyboard XML, resources, assets, DEX files 3 and 4, and all **16 native libraries**. No settings UI, voice class, native decoder, or native local-AI code was edited.

The bounded native scan found no exact checked null-terminated names for `lnk`, `lgp`, `lhk`, `aams`, or `aamv`. This does not constitute universal proof against reflection, dynamically composed names, or indirect Java/native calls.

## Voice issue remains open

The user reported intermittent first-word cutoff, then reported at 20:56:31 UTC that it could not be reproduced and voice seemed to work normally. No verified cause or fix has been established. Stage 23 is **not a voice fix**, and unchanged voice code does not rule out indirect interactions. No recognizer timeout, microphone handling, account access, cloud routing, or voice telemetry was changed.

The diagnostic history remains on `meboard/voice-regression-audit-20260912`, last observed commit `3531051fd2dee882961bf3cf99029fe68c4d8e90`. The issue is tracked as intermittent/currently not reproducible, not closed. No unnecessary reproduction or rollback is requested while the current installation works.

## Reproducibility and public source

An independent first decode/patch/assembly and a clean end-to-end signed driver run from the exact Stage-22 APK produced identical decompressed payloads. This is replay from the pinned Stage-22 binary, **not a new full replay from pristine Gboard**.

- First unsigned APK SHA-256: `3a6753328e751b905261b78114bb17728aa69bd14f37b7e5cc91ff8b738c9456`.
- `classes.dex`: `96f95b1d35471788fbfab7cb8c71aced40c0c57dfa6f5e5dc5adabee4e0ee7ae`.
- `classes2.dex`: `0723c1854a8f2d5671dac9cc1dbc9ecb981c66fb1f3dd9066c5794d71f49d1fc`.

All three new GitHub script blobs match the tested local source files. The existing `MeboardSmaliAssembler.java` is reused unchanged. No private signing key, password, APK, user-learned data, or font binary is included in the public source/report package.

```sh
python tools/build_stage23_test.py \
  --input /path/to/Meboard-stage22-Initial-federated-scheduling-removed-TEST.apk \
  --apktool /path/to/apktool-3.0.3.jar \
  --work /path/to/new-empty-work-directory \
  --output /path/to/stage23-unsigned.apk
```

Pinned Apktool SHA-256: `dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423`. Same-key signing uses `--build-tools`, `--keystore`, `--alias`, and `--password-env` together. Unsigned output is not directly installable. Java 17 or newer and Python 3.10 or newer are required by the supplied build tools.

## Acceptance and next work

Install the signed test as an update without clearing Meboard data, keeping the APK of the currently working version. Stage 22 is the immediate pre-change code rollback; Stage 21 is also retained as the earlier generally working checkpoint. Neither is newly voice-certified.

Check ordinary typing, keyboard switching, learned-word persistence after reopening the host app, Undo, and normal voice use. If the first-word cutoff returns, capture the existing local diagnostic log and note whether the microphone stops or text alone stops updating. Do not mark Stage 23 as a working checkpoint based solely on build or installation success.

Next review: the remaining mixed native-configuration builder `sal.h` and its field consumers, then separable Primes/diagnostic residue. Federated/training-related review inventory, remote-experiment remnants, unresolved networking, and native reporting remain unfinished. No complete absence of outbound telemetry is claimed.
