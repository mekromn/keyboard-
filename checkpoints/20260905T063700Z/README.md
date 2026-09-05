# Meboard checkpoint 20260905T063700Z

This is the authoritative resume point for the device-confirmed `LatinApp.e()` Context-register crash repair.

## Current result

- Exact crashing installed APK identified: **PASS**
- Android 16 fatal stack captured: **PASS**
- Root cause isolated to deleted shared `v7` Context producer: **PASS**
- Physical certificate-whitelist removal preserved: **PASS**
- Full replay from untouched Gboard: **PASS**
- Four DEX files: **PASS**
- Module-registry register/order/constructor gates: **PASS**
- APK Signature Scheme v3: **PASS**
- Stable Meboard signer: **PASS**
- 16 KiB ZIP alignment: **PASS**
- Library upload and byte-for-byte round trip: **PASS**
- Fixed APK installed on Pixel: **NOT YET AT CAPTURE**
- Launcher and `LatinIME` runtime gate: **PENDING**
- Privacy-final status: **NO**

## Fixed candidate

- File: `Meboard-stage16-LatinApp-context-fix-replay-signed.apk`
- SHA-256: `30e0d61df7f88a06d835f61e5f16ed80b204b366e5d968606df777d3f8acd069`
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

Every non-signature ZIP entry in that signed APK is byte-identical after decompression to the successful second clean replay output. The only added records are the three APK signature metadata files.

## Repair boundary

The fix restores only the shared application-`Context` producer needed by later retained startup code. It does not restore the signature-check Runnable, discriminator-8 branch, certificate comparator, exception path, or embedded Google certificate digests. No additional user-facing feature was removed.

## Persistent copies

Library folder: `/Meboard/Checkpoints/20260905T063700Z`

- Public archive SHA-256: `3f4752ac8dc42868badefa9fd36df95040f6e8850f9146a2768511c27efa9264`
- Private archive SHA-256: `3a53857680ac9fb330254cf4bf9add4235d935a8c8e7b22a12f1621631a855d2`
- Fixed APK SHA-256: `30e0d61df7f88a06d835f61e5f16ed80b204b366e5d968606df777d3f8acd069`

The private archive contains proprietary source bytes and signing material. Never publish it.

## Resume action

Install the exact fixed APK over the current same-signer build, verify the installed base APK SHA, launch it, capture a fresh system `AndroidRuntime` log, and then run the `LatinIME` bind/render/type/switch-away/switch-back gate. Do not continue deeper privacy removal until that runtime result is recorded.
