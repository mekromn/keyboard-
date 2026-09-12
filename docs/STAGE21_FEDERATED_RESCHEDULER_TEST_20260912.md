# Meboard Stage 21 — federated completion/retry rescheduler removal

Date: 2026-09-12. Status: **signed test APK; static/build checks PASS; device runtime pending; privacy-final NO**.

## Exact artifact and rollback

| Item | Value |
|---|---|
| New APK | `Meboard-stage21-Federated-rescheduler-removed-TEST.apk` |
| SHA-256 | `c83284fd77f0a99667f39530441ee10391cf185add1cc6e1d64378ba59b41d0e` |
| Size | 110132140 bytes |
| Package | `com.mekromn.meboard` |
| Signer certificate SHA-256 | `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15` |
| Immediate working rollback | `Meboard-stage20-Federated-config-removed-TEST.apk` |
| Stage-20 SHA-256 | `05f16f7e94c17426a988961e15856059ba82b30a30e4dd992ae1d14a757fc7e3` |
| Working checkpoint branch | `meboard/working-stage20-20260912` |
| Working checkpoint commit | `c5323eb9dc12049a140143e61b192921586b576f` |
| Stage-21 test branch | `meboard/stage21-federated-rescheduler-test-20260912` |
| Implementation commit | `4e8134b651940cc3f91ece07c4a2e2596aafb1f6` |

The user reported Stage 20 works at 18:03:59 UTC on 2026-09-12. This is general working feedback, not an exhaustive feature or network audit. The supplied Stage-20 APK was independently re-hashed in the build environment; the installed phone APK was not read back. Stage 20 and the older Stage-19/Stage-16 rollback artifacts were not changed.

## Physical removal

The dedicated **federated completion/retry rescheduler** `lnf` was physically deleted, together with its private construction method `lnk.t(ILjava/lang/String;Llkd;Lynz;I)Lwyv;` and its branch in the shared completion dispatcher.

The dispatcher was reduced from `lnk.f(ILjava/lang/String;Llkd;Lynz;I)Lwzc;` to `lnk.f(ILjava/lang/String;Llkd;I)Lwzc;`. Its federated server-retry-result argument is no longer part of the scheduler API. All three typed call sites were migrated: one in `lkc.d` and two in `InAppJobServiceImpl.onStartJob`.

Only three surviving classes changed: `lnk`, `lkc`, and `InAppJobServiceImpl`. Class count is **21762 -> 21761**; **21758 surviving class files are entirely unchanged**. No classes or no-op implementations were added. Net decoded-smali reduction is **14129 bytes**, including the deleted 12616-byte `lnf` class. APK size stayed the same after packaging/alignment; no APK-size saving is claimed.

### Explicit type boundary

The original discriminator maps type 1 to `FEDERATED_TRAINING_OPTIONS` and type 2 to `PERSONALIZED_TRAINING_OPTIONS`. The reduced dispatcher accepts the existing local/personalized type. An unexpected federated or unsupported type raises `UnsupportedOperationException`, using the existing type-description helper. It is **not** silently routed into local computation and is **not** ignored. This new rejection path has not been exercised on a phone.

The dedicated federated class had only its reviewed private factory as an external typed reference. The factory had only the reviewed dispatcher as a typed caller. No exact `lnf`/`lnk` reflective class-name literal was found in the scanned smali, and no exact checked internal class token was found in the packaged native libraries. These checks are not a universal proof against every possible dynamic lookup.

## Retained behavior and deliberate limits

The local rescheduler `lnc`, its construction method `lnk.u`, and the local interval calculations/settings are unchanged. In the three edited classes, **38 other surviving methods are byte-identical**. The callers' cancellation, unbinding, and job-finish code are unchanged apart from the scheduler argument handoff. The dispatcher's existing asynchronous result handling and monitor cleanup remain unchanged.

This is **not removal of all federated scheduling**. The mixed initial scheduler (`lnk.d` / `lna`), shared interval helper (`lnk.m`), and mixed native-configuration builder (`sal.h`) remain unchanged. They require their own consumer/branch analysis. No native code or configuration protobuf layout was modified in this pass.

## Verification

| Check | Result |
|---|---|
| Exact input APK and guarded decoded-file hashes | PASS |
| Deleted `lnf`, private factory and old dispatch signature references in surviving smali | None |
| Independent comparison of retained local argument routing | 90 cases PASS |
| Unsupported input-type rejection in symbolic dispatcher tests | 6 types PASS |
| Caller migration and unchanged surrounding code | All 3 sites PASS |
| Other surviving methods in modified classes | 38 byte-identical |
| Local rescheduler, interval math/settings and initial scheduler | Unchanged |
| Existing `eqt.aI()` register-state gate | PASS |
| Existing Mozc/Undo/local-computation/anonymous-feedback preservation gate | PASS |
| Current privacy-policy static gate | PASS; zero known fatal findings under that gate |
| DEX assembly, headers, SHA-1 and Adler32 integrity | PASS |
| ZIP CRC integrity | PASS |
| Same signing certificate / APK Signature Scheme v3 | Verified |
| 16 KiB ZIP alignment | PASS |
| Two clean builds from the pinned Stage-20 APK | All 9148 payload entries identical |
| Phone runtime / feature sweep / network capture | NOT RUN |
| Privacy-final | NO |

The 90 cases are symbolic register/argument comparisons, not Android runtime tests. The signature verifier reports v3 verified and v2 not verified; no v2 verification claim is made.

Only `classes.dex` and `classes2.dex` changed. The other **9146 of 9148 non-signature payload entries are byte-identical** to Stage 20, including the manifest, resources, keyboard XML, assets, remaining DEX files, and all **16 native libraries**.

## Reproducibility and source

Both clean driver runs completed successfully. The second unsigned APK reproduces every decompressed payload entry of the signed candidate.

- Unsigned replay SHA-256: `efdbf15b44816b1ebfe1fe661c545f3c98d50193fa7be31dc2b252e5f6214743`
- `classes.dex`: `84122f22758070c2f062f342689d46a005c2bbf013e23070ac62daa00cf81ebf`
- `classes2.dex`: `6d48cbc918971c214914870470d2a7adb8e4148dbb70b870be62f7bbd8795112`

This is replay from the pinned Stage-20 binary, **not a new full replay from pristine Gboard**. All three new GitHub script blobs were checked against the tested local source and match exactly. The existing `MeboardSmaliAssembler.java` is reused unchanged.

```sh
python tools/build_stage21_test.py \
  --input /path/to/Meboard-stage20-Federated-config-removed-TEST.apk \
  --apktool /path/to/apktool-3.0.3.jar \
  --work /path/to/new-empty-work-directory \
  --output /path/to/stage21-unsigned.apk
```

The driver pins Apktool SHA-256 `dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423`. Same-key signing uses `--build-tools`, `--keystore`, `--alias`, and `--password-env` together. No private key, password, proprietary APK, or user-learned data is included in the public source package/repository.

## Acceptance and next work

Install the signed Stage-21 test over Stage 20 without clearing app data. Keep the exact Stage-20 rollback. Check normal typing, switching away/back, learned-word persistence, Undo, voice, clipboard, and usual language/media features. General operation and local-learning persistence both matter for this scheduler change. Stage 21 is not promoted to a working checkpoint until the user reports its result.

Next: classify the federated branches in the initial job-registration path `lnk.d` / `lna`, preserving the local-computation path, then revisit shared interval/configuration consumers. Primes, experiment/diagnostic remnants, unresolved networking, and native reporting removal remain unfinished. No complete absence of outbound telemetry is claimed.
