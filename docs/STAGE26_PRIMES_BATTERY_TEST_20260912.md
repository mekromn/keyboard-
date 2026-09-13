# Meboard Stage 26 — Primes battery reporter removal and APK size audit

Continuation requested: 2026-09-12 23:57:55 UTC. Verification completed during the following UTC day.

Status: **signed test APK; actual-package/static checks PASS; phone runtime pending; privacy-final NO**.

## Exact candidate and working rollback

| Item | Value |
|---|---|
| New APK | `Meboard-stage26-Primes-battery-removed-TEST.apk` |
| SHA-256 | `acd77999d2654af314fbb4fc7b248f986084471564b2a0185dffd26d2d621dd8` |
| APK bytes | **110115756** |
| Exact input / working rollback | `Meboard-stage25-Primes-storage-removed-TEST.apk` |
| Stage-25 SHA-256 | `085171de9c84d7b1001ac956a1fe7f5addbedba4910f5a8bb06e70989299dfda` |
| Stage-25 APK bytes | 110132140 |
| Package | `com.mekromn.meboard` |
| Original signer certificate SHA-256 | `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15` |
| Working checkpoint branch | `meboard/working-stage25-20260912` |
| Working checkpoint commit | `f3d002dc96ff74a5d694e2aee78f48a408359ca4` |
| Test branch | `meboard/stage26-primes-battery-test-20260912` |
| Complete tooling commit | `a16981e286a6043afbc81c3848aa9c0a8e61066a` |

The user confirmed general Stage-25 operation. This is not an exhaustive feature or network audit. The installed phone APK was not read back. The delivered Stage-25 rollback remains unchanged and its hash and signature were rechecked.

## Why APK size stayed the same

The code really became smaller, but ZIP alignment absorbed the savings. Earlier decoded-smali deletion totals were text-source sizes, not compiled-code or archive savings. For example, Stage 25 removed 63806 decoded-smali bytes but only 7664 DEX bytes.

| Measured bytes | Stage 19 | Stage 25 | Stage 26 |
|---|---:|---:|---:|
| Compiled DEX total | 23157088 | 23144644 | 23134604 |
| ZIP local-header extra fields | 181894 | 194338 | 187994 |
| Complete signed APK | 110132140 | 110132140 | 110115756 |

Between Stage 19 and Stage 25, DEX data decreased **12444 bytes** and the first native library's alignment extra field grew by **exactly 12444 bytes**, from 2509 to 14953. Its data stayed at offset 56639488. The APK size was therefore literally unchanged, not merely rounded in the download label.

Stage 26 removes another **10040 compiled bytes**. This crosses the next 16 KiB alignment boundary: the same library now starts at offset 56623104, and its extra field falls to 8609 bytes. Thus **10040 code bytes + 6344 fewer padding bytes = 16384 fewer APK bytes**. Both 110132140 and 110115756 still display as **110.1 MB** when rounded to one decimal place.

Android's official zipalign documentation explains that alignment alters ZIP local-header extra fields and recommends 16 KiB alignment for uncompressed native libraries, with 4-byte alignment for other uncompressed files. This supports direct memory mapping rather than extra copying. Source: https://developer.android.com/tools/zipalign . No compression modes or native-library alignment requirements were changed just to make the APK appear smaller.

Most retained bytes are not the small Java reporting classes: the 16 native libraries total **52469824 bytes**, while `resources.arsc` is **19611312 bytes**. The native total includes the 35950016-byte shared decoder/local-AI library, 11642104-byte Tenor animation library, and 4332136-byte dictation library. They were not deleted because retained features depend on them. This table describes APK bytes, not Android Settings' installed app/data totals.

Stage-19 and Stage-24 figures were observed earlier in this turn after their hashes matched their documented originals. Their local copies later encountered the workspace corruption described below and were excluded from final candidate verification. Stage-25 and Stage-26 figures were remeasured from the valid actual APKs. The evidence package preserves both the original observations and the fresh complete byte-accounting data.

## Physical removal

Four entire dedicated classes were deleted:

| Class | Role | Decoded-smali bytes |
|---|---|---:|
| `tys` | Battery-service construction factory | 4010 |
| `tyr` | Primes battery metric service and lifecycle triggers | 8251 |
| `tyq` | Battery snapshot persistence, differences and metric-report worker | 66671 |
| `tzb` | Detached battery-store provider factory | 1159 |

Total: **80091 decoded-smali bytes and 20 method definitions**. The compiled change is **10040 DEX bytes**: 2128 in `classes.dex` and 7912 in `classes3.dex`.

There are **no edits to surviving classes**, no new classes, and no replacement no-ops. Class count changes **21758 -> 21754**. Fresh independent decodes of the actual signed Stage-25 and Stage-26 APKs confirmed all **21754 surviving class files are byte-identical**.

The typed-reference graph is closed: `tys` has no external typed user; `tyr` is referenced only by that factory and its worker; `tyq` only by the service; `tzb` only by the detached factory. Input hashes and graph guards are checked before deletion. These findings support deletion of a detached reporting cluster, not a claim that it was running or uploading on the phone, or that this change alone improves battery life.

The battery snapshot key and named service implementation marker are absent from every resulting APK payload. Shared battery/statistics helper classes with other consumers remain. This is not a claim that every battery-related metric or native reporter has been removed.

## Verification of the delivered APK

| Check | Result |
|---|---|
| Exact Stage-25 input and four decoded-class hashes | PASS |
| Actual output DEX class/type references | Exactly four classes deleted; no remaining type references; none added |
| Fresh actual-APK decoded class comparison | All 21754 surviving files byte-identical |
| Negative preservation tests | Detect modified survivor or missing deletion |
| Battery snapshot/service markers across all payloads | Absent |
| Existing module-registry register gate | PASS |
| Existing Mozc / Undo / local-computation / feedback gate | PASS |
| Current static privacy gate | PASS; zero known fatal findings under that gate |
| DEX headers, SHA-1 and Adler32 integrity | PASS |
| ZIP CRC integrity and unique entry names | PASS |
| Original certificate / RSA v3 signature / full APK content digest | Independently verified |
| Deliberate signed-payload mutation | Rejected by independent verifier |
| Actual stored-entry offsets | Native 16 KiB and other stored entries 4-byte aligned |
| Independent unsigned rebuild comparison | All 9148 decompressed payload entries identical |
| Phone runtime, voice test and network capture | NOT RUN |
| Privacy-final | NO |

Only **`classes.dex` and `classes3.dex` changed**. The other **9146 of 9148 non-signature payload entries are byte-identical**, including manifest, resources, keyboard XML, assets, DEX files 2 and 4, and all **16 native libraries**. Compression modes are unchanged.

Review-only Primes marker count is now **73**, down from 79 in Stage 25. Other remaining inventory includes federated/training 200 (cap reached), MetricsProcessor 3, Perfetto 22, and Phenotype 108 matches. These are search-marker counts, not proven active tracker counts.

### Native short-name matches

The native scan found the short string `tyr` in two unchanged libraries. Both matches occur in a locale/script table sequence alongside `twm`, `txg`, `txo`, `tyv`, `ude`, `udg`, `udi`, `udm`, and `ug`. The checker pins each library hash, byte offset, `.rodata` section, and surrounding bytes. No matching JVM descriptor was found. The language entries were not deleted. This bounded check is not proof against every dynamically composed or indirect native lookup.

## Workspace integrity incident and recovery

Some local build files, logs and tool copies failed integrity checks during finalization. Their contents were not accepted as evidence. Verification was moved into a RAM-backed workspace. The actual Stage-25 rollback and signed Stage-26 candidate were rehashed, freshly decoded, and compared there; the valid unsigned replay also matches the signed candidate's entire decompressed payload.

A fresh standard `apksigner` CLI run could not be completed with the damaged tool copy. Instead, the supplied independent verifier checked the actual candidate's single-signer v3 RSA/SHA-512 signature, complete chunked APK content digest, certificate/public-key match, and pinned original certificate. It also rejects a deliberately changed payload. This is substantive cryptographic verification, not merely reading the certificate. No fresh successful CLI log or v2 verification is claimed. The verifier is deliberately limited to this checkpoint's signature shape and is not a general replacement for Android's package verifier or device testing.

The files offered for download were separately read back and hashed. No damaged intermediate APK is being offered as a candidate. Original user/Library files were not edited; the integrity problem concerned local working copies.

## Replay and source

- Independent unsigned replay SHA-256: `bb06f0742ecdfb00477f88138721ee46bc9cbab13aeb29b140227c690d8c1875`.
- Output `classes.dex` SHA-256: `e7a359e77b339ce97fe08fc17bfd4d5ea089d85a7b4631977074380a6041b365`.
- Output `classes3.dex` SHA-256: `e56009a3cf8d0ccb2fbe2f6fa2451d64f0a48a0a739b6bcba3acd5cb2e0dd328`.

This reproduces the candidate from the pinned Stage-25 binary, **not a new full rebuild from pristine Gboard**. The scripts include a guarded deletion pass, independent preservation and APK verifiers, pinned build driver, v3 verifier, and exact size auditor. The existing `MeboardSmaliAssembler.java` is reused unchanged.

```sh
python tools/build_stage26_test.py \
  --input /path/to/Meboard-stage25-Primes-storage-removed-TEST.apk \
  --apktool /path/to/apktool-3.0.3.jar \
  --work /path/to/new-empty-work-directory \
  --output /path/to/stage26-unsigned.apk
```

The driver pins Apktool SHA-256 `dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423`. Same-key signing requires the existing private key and the four signing arguments documented in the driver. Unsigned output is not directly installable. The public source/evidence package contains no APK, private key, password, user-learned data, or font file.

## Phone acceptance and remaining work

Install the signed test over Stage 25 without clearing app data; keep the exact Stage-25 APK as rollback. Check ordinary typing, keyboard switching, learned-word persistence, Undo, normal voice use, and usual GIF/download features.

No surviving voice implementation, timeout, microphone handling, account access, or recognizer routing changed. The intermittent first-word cutoff remains open/currently not reproducible; this is not a voice fix. Capture the existing local diagnostic log only if it returns.

Remaining work includes other separable Primes/diagnostic remnants, native-configuration field consumers, remote-experiment remnants, unresolved networking and native reporting. Build and static success do not promote Stage 26 to a phone-verified or privacy-final build.
