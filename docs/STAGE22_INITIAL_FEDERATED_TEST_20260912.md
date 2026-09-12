# Meboard Stage 22 — initial federated scheduling removal

Date: 2026-09-12. Status: **signed test APK; static/build checks PASS; phone runtime pending; privacy-final NO**.

## Exact artifact and working rollback

| Item | Value |
|---|---|
| New APK | `Meboard-stage22-Initial-federated-scheduling-removed-TEST.apk` |
| SHA-256 | `8cf20fabd5ccba93aae7187fa27f4ffe3cbb3bed37a42c73d1e7c34c65db4766` |
| Size | 110132140 bytes |
| Package | `com.mekromn.meboard` |
| Signer certificate SHA-256 | `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15` |
| Immediate working rollback | `Meboard-stage21-Federated-rescheduler-removed-TEST.apk` |
| Stage-21 SHA-256 | `c83284fd77f0a99667f39530441ee10391cf185add1cc6e1d64378ba59b41d0e` |
| Working checkpoint branch | `meboard/working-stage21-20260912` |
| Working checkpoint commit | `e4565f9d39e13848f86e7cec1961ea429ca80f83` |
| New test branch | `meboard/stage22-initial-federated-test-20260912` |
| Complete tested-tooling commit | `db1b9f13a403a179814a1b4b0e09eb154cb62c2f` |

The user reported Stage 21 works on 2026-09-12 at 18:37:41 UTC. This records general working feedback, not an exhaustive feature sweep or network capture. Its delivered APK was independently re-hashed in this build environment; the installed phone APK was not read back. The Stage-21 binary and older rollback artifacts were not changed.

## Physical removal

The initial scheduler `lnk.d(Llgw;)Lwzc;` and its mixed worker `lna` are now specialized to local/personalized jobs. A non-null federated population is explicitly rejected with `UnsupportedOperationException` before namespace preparation, state mutation, or job registration. It is not silently interpreted as local work. The public entry signature remains unchanged.

Four federated-only regions were physically removed from `lna.a(Ltiz;)Lvox;`:

1. Federated-population lookup/replacement preparation.
2. Federated options construction when creating a new job.
3. Federated option/metadata updates in an existing job.
4. Federated options reconstruction when replacing changed job parameters.

Three now-unused worker fields were deleted: the federated/local discriminator `c:Z`, the federated population `e:Ljava/lang/String;`, and federated mode metadata `l:Ltir;`. Their constructor parameters and assignments were removed together; the only constructor call site was migrated to the reduced signature.

The dedicated options builder `lcw.h(Llgw;)Ltis;` and its now-unused enum converter `lcw.g(I)Ltir;` were also physically deleted after checking their remaining callers. No whole shared class or no-op replacement was added. The original local interval helper still receives its ordinary local-mode argument; this is not a retained telemetry enable flag.

Only **three classes changed**: `lnk`, `lna`, and `lcw`. Class count stays **21761**; **21758 complete class files are unchanged**. Net decoded-smali reduction is **10144 bytes**. The signed APK size remains unchanged after packaging/alignment; no APK-size saving is claimed.

## Preserved behavior and limits

The local job-creation/update bodies match the original worker with the four proven-inaccessible federated regions removed. Local URI handling, stored-job comparison, replacement/cancellation cleanup, job submission, and scheduling-failure handling are retained. The local completion/retry rescheduler `lnc` and shared timing helpers `lnk.h` / `lnk.m` were not changed.

Reading or clearing historical federated records is deliberately retained where it participates in replacing an old record with a local job. That is distinct from constructing or registering a new federated job. This pass does not delete the shared serialized-data types, every federated-named setting, every alternative scheduling path, or the native configuration builder.

The guarded original `lgw` constructor distinguishes federated population options from local URI-based options. Static reference scans found only the reviewed `lna` constructor access and builder consumers. No exact checked null-terminated internal class token was found in the 16 packaged native libraries. These are bounded static checks, not a universal proof against all reflection or dynamic Java/native lookup.

## Verification

| Check | Result |
|---|---|
| Exact input APK and pinned decoded-file hashes | PASS |
| Independent local entry/constructor argument comparison | 128 cases matched Stage 21 |
| Accepted versus rejected local test cases | 48 accepted; 80 retained the same invalid-input rejection |
| Nonlocal inputs rejected before registration/preparation | 2 symbolic cases PASS |
| Monitor release and exception cleanup | Matched in reviewed cases; cleanup tail byte-identical |
| Forward local-flag analysis, including exceptional edges | All 4 removed worker regions unreachable for local input |
| Retained worker instruction projection | Exact match |
| Other surviving methods in the 3 changed classes | 236 byte-identical |
| DEX member indexes for deleted fields/builders/old constructor | All absent; new constructor present |
| Existing module-registry register gate | PASS |
| Existing Mozc / Undo / local-computation / feedback gate | PASS |
| Current privacy-policy static gate | PASS; zero known fatal findings under that gate |
| DEX assembly, headers, SHA-1 and Adler32 checks | PASS |
| ZIP CRC integrity | PASS |
| Same signing certificate / APK Signature Scheme v3 | Verified |
| 16 KiB ZIP alignment | PASS |
| Independent clean rebuild payload comparison | All 9148 entries identical |
| Phone runtime / feature sweep / network capture | NOT RUN |
| Privacy-final | NO |

The interpreters verify the reviewed static control flow and argument preparation; they are not an Android VM. The signature verifier reports v3 verified and v2 not verified. No v2 verification claim is made.

Only **`classes.dex` and `classes2.dex` changed**. The other **9146 of 9148 non-signature payload entries are byte-identical** to Stage 21. This includes the manifest, resources, keyboard XML, assets, remaining DEX files, and all **16 native libraries**. No native decoder/local-AI code was modified.

## Reproducibility and public source

The first independent decode/patch/assembly and a second clean end-to-end driver run from the pinned Stage-21 APK produced identical decompressed package payloads. The delivered signed APK was produced by the second driver. This is replay from Stage 21, **not a new full replay from pristine Gboard**.

- First-pass unsigned APK SHA-256: `377a1a777edf39b1db7cbd80a5d993fe675b0e0737abb9e41bddd5bb2531208d`.
- `classes.dex`: `6867f6e5dbd002ee6a1d6e50d78233f002effa119c7b3b50225de665568637e6`.
- `classes2.dex`: `fc60bac989aa62ae027c1842e67167dc73fd08d051f6454cc8c8c787dab7a875`.

All three new GitHub script blobs match the tested local files. The existing `MeboardSmaliAssembler.java` is reused unchanged. Public source and reports contain no private key, password, APK, or user-learned data.

```sh
python tools/build_stage22_test.py \
  --input /path/to/Meboard-stage21-Federated-rescheduler-removed-TEST.apk \
  --apktool /path/to/apktool-3.0.3.jar \
  --work /path/to/new-empty-work-directory \
  --output /path/to/stage22-unsigned.apk
```

Pinned Apktool SHA-256: `dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423`. Same-key signing options are `--build-tools`, `--keystore`, `--alias`, and `--password-env`. Unsigned output is for inspection or subsequent signing, not installation.

## Phone acceptance and next work

Install Stage 22 over Stage 21 without clearing app data. Keep the exact Stage-21 rollback. Check normal typing, switching away/back, learned-word persistence after reopening the host app, Undo, voice, clipboard, and usual language/media features. The explicit nonlocal-input rejection has not been exercised on a phone. Do not treat this build as the working checkpoint until its result is reported.

Next review targets: remaining federated-versus-local timing/configuration branches in `lnk.m` and its callers, then the mixed native-configuration builder `sal.h`. Primes, experiment/diagnostic remnants, unresolved networking, and native reporting cleanup remain unfinished. No complete absence of outbound telemetry is claimed.
