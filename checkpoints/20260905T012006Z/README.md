# Meboard checkpoint 20260905T012006Z

This is the authoritative resume point after a clean APKbox-free replay of the current stage-16 launch-fix pipeline.

## Current result

- Clean source replay: **PASS**
- Four DEX files: **PASS**
- APK Signature Scheme v3: **PASS**
- 16 KiB ZIP alignment: **PASS**
- Static retained-feature gate: **PASS**
- Library upload and byte-for-byte round-trip: **PASS**
- Full Pixel runtime/IME gate: **NOT RUN**
- Privacy-final status: **NO**

Signed launch-test candidate:

- File: `Meboard-stage16-launchfix-replay-signed.apk`
- Size: `110287788` bytes
- SHA-256: `dd8044ae0c365d6e7fbc6a87295cedd6c06bcf87027cdda287b9b9ef8021ffb5`
- Stable signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

## User-facing functionality invariant

No user-facing Gboard functionality is an approved removal target. Preserve every retained keyboard feature and all useful local/on-device AI and personalization. Any privacy patch that breaks a retained feature is failed and must be corrected or rolled back.

The static preservation gate proved:

- all 25 original manifest activities remain;
- input-method, Japanese software-keyboard, and physical-keyboard XML are byte-identical to source;
- 236 retained factories remain in the exact original order with constructor constants preserved;
- no surviving class descriptor references any of the 274 targeted removed classes;
- all 16 retained native libraries are byte-identical to source;
- AAPT badging and runtime resource-table semantics are unchanged from the prior signed candidate.

This is strong static evidence, not a substitute for runtime testing.

## Persistent redundant copies

Library folder:

`/Meboard/Checkpoints/20260905T012006Z`

- Public recovery archive SHA-256: `b2c33a0a9f0fb82d61f9698cbe6cf1156c1c186501d465a3b742a2552a903347`
- Private recovery archive SHA-256: `d18a97cea09dc8559289be6087842eb8ada328e0cabfc0e4f7a3a6de69903314`
- Candidate SHA-256: `dd8044ae0c365d6e7fbc6a87295cedd6c06bcf87027cdda287b9b9ef8021ffb5`

Both recovery archives passed ZIP CRC and per-member SHA-256 verification. The Library-materialized public archive, private archive, and APK were byte-identical to the uploaded local files. The public archive was checked to contain no APK, ASPK, signing key, or keystore material.

The private archive contains proprietary source bytes and the stable signing archive. **Never publish it.**

## Next real gate

1. Install/update the signed candidate manually without APKbox.
2. Verify LatinIME binds and the keyboard renders.
3. Type continuously and confirm the process remains alive.
4. Switch to another keyboard and back.
5. Run the user-facing feature regression sweep.
6. Record the runtime result before any deeper privacy changes.

Do not modify this checkpoint APK. Continue residual Clearcut, Primes, Brella, and Phenotype work on a separate branch only after the runtime gate is recorded.
