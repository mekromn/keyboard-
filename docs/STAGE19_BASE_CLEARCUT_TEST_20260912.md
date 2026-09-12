# Meboard Stage 19 — BaseClearcut removal test

Date: 2026-09-12. Status: **signed test APK; static/build checks passed; runtime pending; privacy-final NO**.

## Exact build and recovery

| Item | Value |
|---|---|
| APK | `Meboard-stage19-BaseClearcut-removed-TEST.apk` |
| Package | `com.mekromn.meboard` |
| APK SHA-256 | `c06c75a38f61baf442f0ed040d03dcd41cec1c45a528184ae7ca4d3be77611d4` |
| Size | 110,132,140 bytes |
| Version name | `18.0.3.954559732-release-arm64-v8a` |
| Version code | `175940518` |
| Signer certificate SHA-256 | `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15` |
| Exact Stage-18 input SHA-256 | `29b41378b2cec4ec805abf9a9dc0fdbdbb8a265d1d089c4b7aa888de896c9ba8` |
| Immutable working Stage-16 rollback SHA-256 | `913b5e69997541ad6015d80661677f510826cfd63980b85a9178a95b71780342` |
| Repository | `mekromn/keyboard-` |
| Branch | `meboard/stage19-base-clearcut-test-20260912` |
| Implementation commit | `11146652293a8bf73f50b58338f74b598bcfb3b7` |

The working rollback was recovered and re-hashed without alteration. Its keyboard rendering and settings had been user-confirmed; this does not establish an exhaustive feature pass. Neither Stage 18 nor this Stage 19 candidate has a recorded device runtime pass. The working baseline and its branch were not promoted or overwritten.

## Physical removals

Eight dedicated classes were deleted, not replaced with no-ops:

| Class | Removed role |
|---|---|
| `prl` | BaseClearcutAdapter implementation |
| `psh` | GoogleKeyboardClearcutAdapter implementation |
| `pri`, `prj`, `prk` | Dedicated adapter event/counter, opt-in, and upload callback helpers |
| `prm` | Clearcut-ready notification |
| `pse` | Dead fallback event/counter collection adapter |
| `psf` | Event container exclusively used by that removed adapter |

Nine shared classes retain their other behavior, with only the reporting/construction branches excised: `daq`, `fjr`, `jdz`, `jea`, `lsn`, `mhc`, `nwk`, `opu`, and `pdm`.

The deleted numeric switch cases are `daq:2`, `lsn:17,18`, `pdm:9`, `fjr:12`, and `nwk:17`. Their tables are converted to sparse switches, rather than mapping removed selectors to a different feature. Conditional/default reporting branches are excised from `mhc:3`, `opu:2`, `jdz:3`, and `jea:4`, after review of their producers.

A shared register constant in `mhc` is explicitly retained because the surviving dictation branch also consumes it. Matching short names in the guarded `fws` locale map are language/locale identifiers, not reflective class lookups, and remain unchanged.

Class count: **21,770 -> 21,762**. No classes were added. **21,753 surviving class files are entirely unchanged**; nine contain the narrow edits above. Net decoded-smali reduction is 79,628 bytes. This is not a compressed-APK size claim.

## Artifact boundary

The signed input and output contain the same **9,148 non-signature payload entries**. Only `classes.dex` and `classes2.dex` changed. The other **9,146 entries are byte-identical**, including the manifest, resource table, keyboard XML, assets, secondary DEX files 3 and 4, and all 16 native libraries.

The shared native library remains unchanged:
`libintegrated_shared_object.so` SHA-256 `1dce4b3d9424d63c6fd6917fedb8b3c7fca37db8bde43c82dc4ed1120114a836`.

The retained Japanese/Mozc, Undo, local-learning, local-computation, dictation, GIF/sticker, and explicit anonymous-feedback entry points were not intentionally removed. Static preservation is not proof that all those features work on-device.

## Checks performed

| Check | Result |
|---|---|
| Exact Stage-18 input hash and exact target-file hashes | PASS |
| Deleted descriptors absent from surviving smali | PASS |
| BaseClearcutAdapter marker absent | PASS |
| No new classes; exact eight-deletion/nine-edit scope | PASS |
| Independent comparison of 88 retained numeric switch cases | PASS |
| Independent comparison of four retained conditional tails | PASS |
| Shared dictation register constant | PASS |
| Existing `eqt.aI()` register-state gate | PASS |
| Existing Stage-18 Mozc/Undo/local-computation/feedback preservation gate | PASS |
| Current privacy-policy static gate | PASS; zero fatal findings under that gate |
| Both affected DEX files assembled; header, SHA-1 and Adler32 checks | PASS |
| ZIP integrity | PASS |
| Same original signer; APK Signature Scheme v3 verification | PASS |
| 16 KiB ZIP alignment | PASS |
| Independent clean Stage-19 replay from pinned Stage-18 APK | PASS; every payload entry identical |
| Device runtime/feature test and network capture | NOT RUN |
| Privacy-final | NO |

The actual signature verifier reports v3 verified and v2 not verified. No v2 verification claim is made.

## Reproducibility

The tested scripts are `remove_base_clearcut_stage19.py`, `verify_base_clearcut_stage19.py`, `MeboardSmaliAssembler.java`, and `build_stage19_test.py`. Their GitHub blob hashes match the local tested files.

A second clean decode/build from the exact Stage-18 APK reproduced all 9,148 decompressed payload entries of the signed delivered candidate. The unsigned replay APK SHA-256 is `b7620b23a69a41c5f3a21336cc7676a8f65db7c10d7b3a055f269d9e51ab1edd`.

This proves replay from the pinned Stage-18 binary, **not a new full replay from pristine Gboard**. The new driver deliberately avoids older broad Stage-18 removal scripts.

Pinned Apktool 3.0.3 SHA-256:
`dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423`.

Run with Java 17 or newer, Python 3.10 or newer, and the pinned tool:

```sh
python tools/build_stage19_test.py \
  --input /path/to/Meboard-stage18-Mozc-reporting-sinks-test.apk \
  --apktool /path/to/apktool.jar \
  --work /path/to/new-empty-work-directory \
  --output /path/to/stage19-unsigned.apk
```

For same-key signing, the driver also accepts `--build-tools`, `--keystore`, `--alias`, and `--password-env` together. Supply the existing private Meboard key locally. No key or password is included in the public source/evidence package. Unsigned output is for inspection or subsequent signing, not installation.

## Runtime acceptance and next removal

Keep the working rollback before testing. Install the signed test as an update to same-signer Meboard, without clearing its data. Test keyboard rendering, continuous typing, switching to Gboard and back, autocorrection Undo, Japanese conversion/candidates, learned-word persistence, clipboard, dictation, GIF/sticker use, settings, and the explicit feedback screens. Record the exact installed APK hash and any failure. Do not promote this build based only on successful installation.

Idle/ordinary-typing network capture and separate deliberately invoked online-feature tests are still needed. No complete absence of outbound telemetry is claimed.

Next: isolate the federated-only endpoint/flag branch in the mixed trainer configuration without deleting local-computation flags. Residual Primes, Phenotype, diagnostic, and native code still require consumer/reachability review. The broad remaining marker counts are review inventory, not confirmed active trackers. Native surgery stays separate until indirect-call and registration analysis establishes a safe deletion boundary.
