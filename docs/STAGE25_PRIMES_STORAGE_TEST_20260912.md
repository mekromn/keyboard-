# Meboard Stage 25 — Primes storage-statistics removal

Date: 2026-09-12. Status: **signed test APK; static/build checks PASS; phone runtime pending; privacy-final NO**.

## Exact artifact and working rollback

| Item | Value |
|---|---|
| New APK | `Meboard-stage25-Primes-storage-removed-TEST.apk` |
| SHA-256 | `085171de9c84d7b1001ac956a1fe7f5addbedba4910f5a8bb06e70989299dfda` |
| Size | 110132140 bytes |
| Package | `com.mekromn.meboard` |
| Version code | `175940518` |
| Signer certificate SHA-256 | `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15` |
| Exact input / working rollback | `Meboard-stage24-Provider-stats-removed-TEST.apk` |
| Stage-24 SHA-256 | `d7c77f87c45eca6a91f7c5bdfcc0667f287c87f09c57890563609a5376bb5d46` |
| Working checkpoint branch | `meboard/working-stage24-20260912` |
| Working checkpoint commit | `6bf5ccb48967d7d83a387e07f1fa533b5c96e66a` |
| Stage-25 test branch | `meboard/stage25-primes-storage-test-20260912` |
| Complete tested-tooling commit | `290bf56a2b2e243fd1fecad75e3f400c8d0888ab` |

The user reported Stage 24 works at 22:29:09 UTC on 2026-09-12. This is general working feedback, not an exhaustive feature sweep or network audit. The delivered input and new output were independently re-hashed in this build environment. The installed phone APK was not read back. The Stage-24 APK and all earlier working/checkpoint branches remain unchanged.

## Finding and physical removal

The remaining Primes storage reporter has a dedicated lifecycle service (`udo`), reporting worker (`udn`), and directory-traversal entry/helper (`udh`). The worker queries package/storage statistics, traverses directories to gather names/sizes, constructs storage metrics, and passes the result to the shared metric recorder. It also maintains `primes.packageMetric.lastSendTime` for report throttling.

All **three classes are physically deleted**, including their collection, traversal, record-construction, timing/state handling, callbacks, and implementation bodies. Their unused storage-specific constructor and construction branch are removed from the shared `tgh` factory. This is not just deletion of names or disabling a setting.

The only surviving class modified is **`tgh`**. Its original branches 0 through 6, dispatch mapping, register setup, and four remaining constructors are unchanged. The former storage-reporter default now throws `UnsupportedOperationException` for an unsupported selector; it does not return a no-op or construct a different feature. That rejection is a defensive boundary, not a newly tested Android runtime path.

The exact typed-reference graph is closed: `udo` is referenced only by its worker and the reviewed factory; `udn` only by the service; `udh` only by the worker. The only external typed user of the shared factory is `pli`. A separate forward control-flow check found four construction sites with selectors **3, 0, 2, 1**; none selects the deleted default. The storage-specific constructor had no typed callers. The patch rejects changes to these input files or reference relationships before writing.

This establishes a separable, currently detached reporting cluster in the inspected Java code. It does **not** prove the reporter previously ran or uploaded anything on the phone, and it is not universal proof against arbitrary reflection or dynamically generated native lookups.

Class count changes from **21761 to 21758**. **21757 surviving class files are entirely unchanged**. No classes or methods were added, and no no-op implementation was introduced. The three deleted class files total **61584 decoded-smali bytes**; net decoded-smali reduction including the factory edit is **63806 bytes**. The APK size remains unchanged after packaging/alignment; no APK-size saving is claimed.

## Verification results

| Check | Result |
|---|---|
| Exact Stage-24 input and guarded decoded-file hashes | PASS |
| Deleted classes / old constructor in compiled DEX indexes | Absent |
| Exact compiled class-definition delta | Only `udo`, `udn`, `udh` deleted; none added |
| Retained shared-factory case bodies and mapping | All 7 byte-identical |
| Retained shared-factory constructors | All 4 byte-identical |
| Existing typed factory construction sites | All 4 proven to select retained branches |
| Deliberately changed reporting selector | Rejected by the independent verifier |
| References to deleted class descriptors in surviving smali | None |
| Package-statistics report marker and capture implementation names in APK payloads | Absent |
| Existing module-registry register-state check | PASS |
| Existing Mozc / Undo / local-computation / feedback static gate | PASS |
| Current privacy-policy static gate | PASS; zero known fatal findings under that gate |
| DEX assembly, headers, SHA-1 and Adler32 integrity | PASS |
| ZIP CRC integrity | PASS |
| Original signer / APK Signature Scheme v3 | Verified |
| 16 KiB ZIP alignment | PASS |
| Independent first build versus clean signed rebuild | All 9148 payload entries identical |
| Phone runtime / voice test / network capture | NOT RUN |
| Privacy-final | NO |

The factory and caller proofs are static comparisons and bounded control-flow analysis, not Android execution. Successful assembly and signature verification do not establish complete ART/runtime correctness. The actual signing verifier reports v3 verified and v2 not verified; no v2 verification claim is made.

Only **`classes.dex` and `classes3.dex` changed**. The other **9146 of 9148 non-signature payload entries are byte-identical** to Stage 24, including the manifest, keyboard XML, resources, assets, DEX files 2 and 4, and all **16 native libraries**. The native local-computation configuration builder and the security-provider installation code changed in no way in this pass.

The current static inventory's Primes marker count decreased from the previously recorded 87 to **79**. Other review-only counts are federated/training **200 (cap reached)**, MetricsProcessor **3**, Perfetto **22**, and Phenotype **108**. These are marker matches, not counts of confirmed active trackers.

## Native scan: reviewed accidental match

The bounded null-terminated-token scan found no exact checked names/descriptors for the three deleted classes in the 16 native libraries. It did find the retained factory's short name `tgh` as accidental bytes in `libtenoranimation_jni.so`.

That hit was investigated rather than silently ignored: byte offset **0x1efb84** is the first 32-bit field of entry **18841** in the ELF `.eh_frame_hdr` unwind index, whose header declares **32742** entries. It is not a string-table entry or a JNI class-name string. The binary verifier checks the exact library hash, location, ELF section, and table encoding before accepting this one finding. Any new match fails the check.

Tenor library SHA-256: `ec3dd77ce6708b7544c3cfa7f9e23a9cd1048af5646d43faf71b5518f23efdc8`. No bytes in that library or any other native library were modified. This bounded scan does not certify the rest of the native code or dynamically composed class names.

## Replay and source

The first decode/patch/assembly and a second clean end-to-end signed driver run from the exact Stage-24 APK produced identical decompressed payloads. The delivered signed APK is the second build. This is replay from the pinned Stage-24 binary, **not a new full rebuild from pristine Gboard**.

- First unsigned APK SHA-256: `5433dff456418540ea4ba4a0fd04bbeda49c78084b3e43169d329bc7875d5b49`.
- `classes.dex`: `456531008629db12b38f80953368980a068fd8b931e06b3c34988e3f92ccadd6`.
- `classes3.dex`: `269da9512f59c2266049f9e9c3367e4fee07e7f700bc2e9429ac280666b3ec1f`.

All four new GitHub script blobs match the actual tested local files. `MeboardSmaliAssembler.java` is reused unchanged. The source/evidence ZIP contains no private key, password, APK, user-learned data, or font file.

```sh
python tools/build_stage25_test.py \
  --input /path/to/Meboard-stage24-Provider-stats-removed-TEST.apk \
  --apktool /path/to/apktool-3.0.3.jar \
  --work /path/to/new-empty-work-directory \
  --output /path/to/stage25-unsigned.apk
```

The driver pins Apktool SHA-256 `dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423`. Same-key signing uses `--build-tools`, `--keystore`, `--alias`, and `--password-env` together. Unsigned output is for inspection/subsequent signing, not installation. The supplied tools require Java 17 or newer and Python 3.10 or newer.

## Phone acceptance and remaining work

Install Stage 25 as an update without clearing Meboard data; keep the exact Stage-24 APK as rollback. Check ordinary typing, keyboard switching, learned-word persistence, Undo, normal dictation and your usual GIF/download/online features. Stage 25 is not promoted to a working checkpoint until its result is reported.

No voice implementation, timeout, microphone handling, account access or recognizer routing was changed. The intermittent first-word cutoff remains open/currently not reproducible; Stage 25 is not a voice fix. Capture the existing local diagnostic log only if it returns.

Remaining work includes other separable Primes reporters and diagnostic remnants, mixed native-configuration field consumers, unresolved networking and native reporting. Shared storage configuration classes were not removed wholesale. Removing this reporter does not make the whole keyboard or external service providers telemetry-free.
