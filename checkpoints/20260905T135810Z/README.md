# Meboard checkpoint 20260905T135810Z

This is the authoritative resume point after repairing the device-confirmed `LatinIME` keyboard-definition resource crash.

## Exact failure

The prior candidate bound the IME service and then crashed repeatedly with:

```text
Failed to fetch keyboard for prime when activating
Caused by: java.lang.IllegalStateException: Failed to get identifier from name: 0
```

The monolithic APK had copied xxhdpi split assets without merging all fixed split resource IDs. Base-only decoding had also converted split-backed references to `@null`.

## Exact repair

- Restored **114** density-split public IDs at their original values.
- Restored **194** original nonzero XML references across **48** resources.
- Added a binary verifier requiring every repaired attribute to compile as a real reference to the exact original target ID.
- Confirmed **zero** original nonzero references remain zero.

## Candidate

- File: `Meboard-stage16-density-resource-fix-replay-signed.apk`
- Package: `com.mekromn.meboard`
- Size: `110304172` bytes
- SHA-256: `913b5e69997541ad6015d80661677f510826cfd63980b85a9178a95b71780342`
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

## Verification

- Two clean replays from the untouched source: **PASS**
- Replay using the exact committed repair script: **exit 0**
- Replay and promoted candidate ZIP payload: **9,148/9,148 entries byte-identical**
- Four DEX files: **PASS and byte-identical to the previous candidate**
- Sixteen native libraries: **PASS and byte-identical to the previous candidate**
- ZIP integrity, APK Signature Scheme v3, stable signer, and 16 KiB alignment: **PASS**
- `eqt` registry, constructor constants, and `LatinApp.e()` Context-register gates: **PASS**
- Compiled density resource-ID/reference gate: **PASS**
- Pixel `LatinIME` render/type/switch gate: **PENDING**
- Privacy-final status: **NO**

No application bytecode, native code, account-isolation logic, telemetry-removal logic, local-AI path, or user-facing feature implementation was changed by this repair. Only the broken resource table and affected XML resource payloads changed.

## Redundant recovery

Library folder: `/Meboard/Checkpoints/20260905T135810Z`

- Public archive SHA-256: `54659eadbe8846f9f18c98da1a5b051792e28ed6f870ba20d8a7a89364c154ad`
- Private archive SHA-256: `4f41d00058f5f01c603bc6e70a336da81431116a03d71be73703200edcc6d3b0`
- APK SHA-256: `913b5e69997541ad6015d80661677f510826cfd63980b85a9178a95b71780342`

The public archive contains no APK, ASPK, signing key, or keystore. The private archive contains proprietary source/artifacts and stable signing recovery material and must never be published. The public archive, private archive, and APK were materialized back from Library and verified byte-for-byte; both archives passed ZIP CRC again.

## Resume action

Install the exact candidate over the current same-signer Meboard build. Verify the installed base APK SHA, invoke Meboard in a text field, capture a fresh system log, and require keyboard render, continuous typing, switch-away, and switch-back survival. Do not continue deeper privacy removal until that runtime result is recorded.
