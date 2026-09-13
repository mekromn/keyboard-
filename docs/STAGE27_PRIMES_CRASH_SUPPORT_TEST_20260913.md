# Meboard Stage 27 — Primes crash-report support removal

Date: 2026-09-13 UTC. Status: **signed test APK; static/build checks PASS; phone runtime pending; privacy-final NO**.

## Exact artifact and rollback

- APK: `Meboard-stage27-Primes-crash-support-removed-TEST.apk`
- SHA-256: `1827fc3a917f28d466f6572e3967acd669f5836df1e8cb2d432adb58c3d66841`
- Size: 110115756 bytes.
- Package: `com.mekromn.meboard`.
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`.
- Exact Stage-26 input/rollback SHA-256: `acd77999d2654af314fbb4fc7b248f986084471564b2a0185dffd26d2d621dd8`.
- Preserved working branch: `meboard/working-stage26-20260913`, commit `7262291e5c131847ac069504e482afe128660ce0`.
- Test branch: `meboard/stage27-crash-support-test-20260913`.
- Complete tested tooling commit: `79429191dcd80d84008be559059b108e1e0f0836`.

The user confirmed Stage 26 works at 01:21:48 UTC and requested continuation at 01:25:44 UTC. This is general feedback, not an exhaustive feature/network audit. The original Stage-26 attachment was re-hashed and is unchanged. The installed phone APK was not read back. Existing older checkpoints are untouched.

The Stage-26 repository branch was present at `7906b04b1b0c573a38b673da59796fddc31105d1`; this was the observed source base. Stage-27 source and its working-checkpoint record were successfully committed in this turn.

## Physical removal

Nine entire classes were deleted:

| Classes | Removed function |
|---|---|
| `uec` | CrashMetricFactory: crash-metric construction and process-statistics attachment |
| `uai`, `udx`, `ued` | Factories producing the deleted `uec` implementation |
| `uag` | Detached crash-support construction factory |
| `uad` | Context supplier including the `primes/crash` directory path |
| `uae`, `uaf`, `uaq` | Dependency factories in the same crash-support chain |

Every typed reference to the nine classes lies inside the deletion set. Exact source hashes and inbound-reference relationships are checked before deletion. No exact class-name literal was found in the scanned smali, and no exact NUL-delimited target name/descriptor was found in any of the 16 packaged native libraries. These are bounded static checks, not universal proof against dynamically composed or indirect lookups.

Shared dependencies `uab`, `acjw`, `mcx`, and `uiz` have retained consumers and remain unchanged. This removes detached crash-report support, **not every crash reporter or diagnostic component**. Android crash handling is not modified. No claim is made that these components previously ran or uploaded on this phone.

Class count: **21754 -> 21745**. All **21745 surviving class files are byte-identical**, also verified by freshly decoding the signed output. No new class, method, rejection path, forced flag or no-op implementation was introduced. Removed source: **19013 smali bytes / 26 method definitions**. Compiled DEX reduction: **3032 bytes**.

## Artifact and feature boundary

Only **`classes.dex` changed**. The other **9147 of 9148 non-signature payload entries are byte-identical**: manifest, keyboard resources, resource table, assets, DEX files 2–4 and all **16 native libraries**. Compression methods are unchanged.

Voice implementations, recognizer settings, local computation, local-learning code and anonymous feature networking were not edited. The first-word voice cutoff remains open/currently not reproducible. This is not a voice fix or a comprehensive runtime preservation certification.

## Checks actually performed

| Check | Result |
|---|---|
| Pinned input APK and nine source-file hashes | PASS |
| Closed original typed-reference graph | PASS |
| Compiled class-definition delta | Exactly nine deleted; none added |
| Removed descriptors in compiled DEX type indexes | Absent |
| CrashMetricFactory and `primes/crash` markers throughout APK payloads | Absent |
| Independent decoded-source comparison | All 21745 survivors byte-identical |
| Fresh decode of actual signed output | Same exact nine deletions; no survivor edits |
| Three negative tests: retained-file descriptor, target drift, changed survivor | Rejected; test trees restored and reverified |
| Existing module-registry register gate | PASS |
| Existing Mozc / Undo / local-computation / feedback gate | PASS |
| Current privacy-policy static gate | PASS; zero known fatal findings under that checker |
| DEX headers, SHA-1, Adler32 and ZIP CRCs | PASS |
| Original certificate and APK v3 signature | Verified |
| Actual stored-native 16-KiB / other stored-entry 4-byte alignment | PASS |
| Independent public-driver replay | All 9148 payload entries match signed artifact |
| Phone runtime / dictation / network capture | NOT RUN |
| Privacy-final | NO |

The tests do not execute ART or Android services. Signature verification reports v3 true and v2 false; no v2 verification claim is made. Review-only marker counts: Primes 71, federated/training 200 (cap reached), MetricsProcessor 3, Perfetto 22 and Phenotype 108. Those are pattern counts, not active-tracker counts.

## Size accounting

| Bytes | Stage 26 | Stage 27 |
|---|---:|---:|
| Compiled DEX total | 23134604 | 23131572 |
| ZIP local extra/alignment space | 187994 | 191026 |
| Signed APK | 110115756 | 110115756 |

Code shrank **3032 bytes** and alignment padding grew **3032 bytes**, leaving the exact APK size unchanged. No storage-saving claim is made. Native alignment and retained functionality were not reduced to alter the size label.

## Reproducibility

The first driver timed out during assembly; assembly was restarted from its verified patched tree and then packaged/signed. Two subsequent independent unsigned driver runs completed end-to-end from fresh Stage-26 decodes and reproduced the signed payload. The final public driver was exercised in the latter run. The interrupted attempt is not counted as an uninterrupted successful build.

- Public-driver unsigned APK SHA-256: `0d68a18e01bd54e82cfefe7c636250d198250605e4cae83de41a247446ec4eba`.
- New main DEX SHA-256: `62548ffde7e9aca731a53b70fc88efe40f8c34af06097111a690012612c69f43`.
- Actual recovered Apktool 3.0.3 SHA-256: `dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423`.
- Actual apksigner JAR SHA-256: `2defad215d7ff52968a409cde528cdaef7918b115e276b8e3378ca7a178e4180`.

The measured Apktool hash differs from the alternate recovered hash in the earlier local Stage-26 report. This driver pins the tool actually used here; input APK and target source hashes are separately guarded. This is replay from Stage 26, not a full new rebuild from pristine Gboard. All seven delivered tool-source blobs match their remote counterparts at the complete tooling commit. The Java assembler is reused unchanged.

```sh
python tools/build_stage27_test.py \
  --input /path/to/Meboard-stage26-Primes-battery-removed-TEST.apk \
  --apktool /path/to/the-pinned-apktool.jar \
  --work /path/to/new-empty-work-directory \
  --output /path/to/stage27-aligned-unsigned.apk
```

The public driver produces aligned **unsigned** output; signing is a separate local step. The delivered test APK is already signed. The repository and source/evidence package contain no signing credentials, proprietary APK, native library, learned user data, or font file.

## Acceptance and remaining work

Install the signed test as an update without clearing Meboard data. Keep the exact Stage-26 APK as rollback. Check ordinary typing, keyboard switching, learned-word persistence, Undo, dictation and usual GIF/download features. Do not promote Stage 27 based only on build or installation success.

Remaining work includes Primes network/memory/jank reporters and mixed factories, diagnostic remnants, native configuration field consumers and native reporting. Shared classes require branch-level review. No whole-app absence of telemetry or completeness of privacy removal is claimed.
