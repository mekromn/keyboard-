# Meboard Stage 24 — security-provider request-statistics removal

Date: 2026-09-12. Status: **signed test APK; static/build checks PASS; phone runtime pending; privacy-final NO**.

## Exact artifact and working recovery point

| Item | Value |
|---|---|
| New APK | `Meboard-stage24-Provider-stats-removed-TEST.apk` |
| SHA-256 | `d7c77f87c45eca6a91f7c5bdfcc0667f287c87f09c57890563609a5376bb5d46` |
| Size | 110132140 bytes |
| Package | `com.mekromn.meboard` |
| Signer certificate SHA-256 | `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15` |
| Immediate working rollback/input | `Meboard-stage23-Federated-timing-removed-TEST.apk` |
| Stage-23 SHA-256 | `08073c39f009b7679c36fa1a4364d42fe945b755ac66062627da85a65351d401` |
| Working checkpoint branch | `meboard/working-stage23-20260912` |
| Working checkpoint commit | `c7343624cd5b93aa2d397a110e5c31f9f44ec1b8` |
| New test branch | `meboard/stage24-provider-stats-test-20260912` |
| Complete tested-tooling commit | `762d096b78fa1a54db4b7c581d2915fec8c2cc4a` |

The user reported Stage 23 works at 22:13:50 UTC on 2026-09-12. This is general user feedback, not a complete feature sweep or network audit. The input attachment and new output were independently re-hashed in the build environment. The installed phone APK was not read back. Stage 23 and older rollback binaries/branches remain unchanged.

## Finding and exact physical removal

Review of the retained local-computation setup found a separate reporting branch in `InAppTrainingServiceImpl`. On a security-provider fallback path, it collects the app context and two uptime timestamps, packages them as reflective arguments, loads `com.google.android.gms.common.security.ProviderInstallerImpl`, and calls its `reportRequestStats2` method. The return value is discarded. An ordinary exception in the reporting operation is logged and provider installation continues.

This is a concrete, separable statistics handoff. It is not needed to construct or insert the security provider. No device network capture was performed: the evidence establishes the packaged reporting path, not that it ran or uploaded anything on this phone. The implementation supplied by the external Google Play services package was not inspected.

This pass physically removes:

1. Both report-only `SystemClock.uptimeMillis()` captures.
2. The report-only initialized-state read and dispatch condition.
3. The report argument array, context/long wrappers, class loading and `reportRequestStats2` invocation.
4. The report-only exception handling/log-message construction.
5. The now-unreferenced `qqg.o(J)Lqqg;` long-argument wrapper method, after checking that its only two typed callers belonged to the removed branch.

No whole shared class, replacement no-op, forced telemetry flag, or new method was added. Exactly **two class files changed**: `InAppTrainingServiceImpl` and `qqg`. Class count remains **21761**; **21759 complete class files are unchanged**. Net decoded-smali reduction is **2714 bytes**. APK size is unchanged after packaging/alignment; no APK-size saving is claimed.

## What is preserved

Provider discovery, Google Play services availability checks, the Dynamite provider path, the fallback package context, cached-provider state, actual `insertProvider` setup, and their retained error/lock-cleanup paths remain. The provider installation helper `lrz.a` is byte-identical. This change does not disable security-provider installation or replace it with a success stub.

The general reflection utility `lcw.bd` remains because other retained HTTP/provider code uses it. Only the newly unreferenced long-argument adapter was removed from the shared `qqg` class. All **47 other methods in the two edited classes are byte-identical**. The long local-computation body after the edited setup region is unchanged, including native-runner invocation and completion cleanup.

### Why the native configuration builder was not changed

The inspected `sal.h(Llgp;String)` result is serialized and passed directly into `NativeLCRunnerWrapper.runNative` in the retained local-computation path. Its fields cannot be removed merely because they have training-related names. No per-field native-consumer proof was completed in this pass. The builder, its configuration defaults, serialized message layout and all native libraries are unchanged. The separate statistics callback above provided a narrower removal without guessing about native behavior.

## Verification results

| Check | Result |
|---|---|
| Exact input APK, two class hashes and edited-method hash | PASS |
| Deleted helper references in surviving smali and compiled DEX method indexes | Absent |
| `reportRequestStats2` and report-error string across every APK payload | Absent |
| Independent retained provider-prefix comparisons | 224 modelled scenarios matched |
| Scenario coverage | Enabled/disabled, cached/uncached, module/fallback availability, selected setup/install/report exceptions |
| Retained externally observable calls and live boundary registers | Matched in the reviewed scenarios |
| Lock/monitor balance | No retained lock at either tested exit |
| Deliberately wrong fallback-provider identity | Detected by the verifier |
| Reporting calls and uptime captures in the new simulated prefix | Zero |
| Other methods in edited classes | 47 byte-identical |
| Shared reflection utility, native configuration builder and installer helper | Unchanged |
| Existing module-registry register gate | PASS |
| Existing Mozc / Undo / local-computation / feedback static gate | PASS |
| Current privacy-policy static gate | PASS; zero known fatal findings under that gate |
| DEX assembly, headers, SHA-1 and Adler32 integrity | PASS |
| ZIP CRC integrity | PASS |
| Same signer / APK Signature Scheme v3 | Verified |
| 16 KiB ZIP alignment | PASS |
| Independent first build versus clean signed rebuild | All 9148 payload entries identical |
| Phone runtime / voice / network capture | NOT RUN |
| Privacy-final | NO |

The interpreter models external provider calls rather than executing Android or Google Play services. Of its 224 scenarios, eight exercise the original report handoff; those reports disappear while the retained outcome remains matched. It checks normal and selected exceptional paths, not every possible runtime failure. Register liveness includes conservative exception edges. The first timestamp values are not live at the retained comparison boundaries. The signature verifier reports v3 verified and v2 not verified; no v2 claim is made.

Only **`classes.dex` and `classes2.dex` changed**. The other **9146 of 9148 non-signature payload entries are byte-identical** to Stage 23. This includes the manifest, resources, keyboard XML, assets, DEX files 3 and 4, and all **16 native libraries**. Class-definition sets in all four DEX files are unchanged.

The native monolith remains SHA-256 `1dce4b3d9424d63c6fd6917fedb8b3c7fca37db8bde43c82dc4ed1120114a836`. A bounded scan found no exact checked null-terminated `qqg`, `Lqqg;`, or `reportRequestStats2` tokens in the packaged native libraries. This is not universal proof against dynamically composed names or indirect lookup.

## Replay and public source

An independent first decode/patch/assembly and a second clean end-to-end signed build from the exact Stage-23 APK produced identical decompressed payloads. The delivered signed APK is the second build. This proves replay from the pinned Stage-23 binary, **not a fresh full rebuild from pristine Gboard**.

- First unsigned APK SHA-256: `b35e0705caa9ada23d6796fdf3f0a0f29a3e80d7dc8358ca572be26748f10e90`.
- `classes.dex`: `6d189b9ea8efe15d5e02ca5ae18ab555249b79007986a2c6157d8b208d6bffa2`.
- `classes2.dex`: `124965fcfbfa486afd46602dbc49aa9ce28e31c5fd839c31ce7b69040a08106f`.

The three new GitHub script blobs match the tested local files. The existing `MeboardSmaliAssembler.java` is reused unchanged. The source/evidence package contains no private key, password, proprietary APK, user-learned data, or font file.

```sh
python tools/build_stage24_test.py \
  --input /path/to/Meboard-stage23-Federated-timing-removed-TEST.apk \
  --apktool /path/to/apktool-3.0.3.jar \
  --work /path/to/new-empty-work-directory \
  --output /path/to/stage24-unsigned.apk
```

Pinned Apktool SHA-256: `dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423`. Same-key signing uses `--build-tools`, `--keystore`, `--alias`, and `--password-env` together. Unsigned output is not directly installable. The provided toolchain requires Java 17 or newer and Python 3.10 or newer.

## Phone acceptance and remaining work

Install the signed Stage-24 test over Stage 23 without clearing app data. Keep the exact Stage-23 APK as rollback. Check normal typing, keyboard switching, learned-word persistence, Undo, ordinary voice use and retained online features. Build success is not a phone-runtime pass; Stage 24 is not promoted to a working checkpoint yet.

The intermittent first-word voice cutoff remains open/currently not reproducible. No voice implementation, timeout, microphone handling, account access, or recognizer routing was changed. This build is not a voice fix. Capture a local diagnostic log only if the symptom returns.

Next: review separable Primes/diagnostic remnants while continuing field-by-field analysis of the native configuration path. Native reporting, remote-experiment remnants and unresolved networking remain unfinished. Removing this one reporting handoff does not establish that external providers or the whole keyboard are telemetry-free.
