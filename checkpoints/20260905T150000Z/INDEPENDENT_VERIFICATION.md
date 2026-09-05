# Meboard independent density-resource verification — 20260905T150000Z

Candidate: `Meboard-stage16-density-resource-fix-replay-signed.apk`

- APK SHA-256: `913b5e69997541ad6015d80661677f510826cfd63980b85a9178a95b71780342`
- Stable signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`
- Package: `com.mekromn.meboard`
- Label: `Meboard`

A second verifier, independent of the build and committed density verifier, checked the promoted APK directly against the untouched Gboard base APK, the xxhdpi split, the complete 194-record loss manifest, and the prior IME-starting candidate.

## Result: PASS

- APK Signature Scheme v3: verified
- RSA key size: 4096 bits
- ZIP integrity: passed
- 16 KiB ZIP/native alignment: passed
- DEX set: `classes.dex`, `classes2.dex`, `classes3.dex`, `classes4.dex`
- All four DEX payloads byte-identical to the prior IME-starting candidate
- All 16 native libraries byte-identical to the prior IME-starting candidate
- Density-split fixed public IDs checked at exact upstream IDs: **114/114 passed**
- Previously lost nonzero compiled XML references: **194/194 restored to exact upstream IDs**
- Known intentional null references: **88/88 remained null**
- Original nonzero references still compiled as zero: **0**

This verifies static/resource correctness only. The exact installed APK must still pass the Pixel 9 Pro XL `LatinIME` bind, render, continuous typing, switch-away, and switch-back runtime gate before it is promoted as working. Privacy-final status also remains false pending the later native and outbound-reporting removal gates.
