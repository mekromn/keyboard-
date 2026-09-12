# Meboard Stage-19 user-confirmed working checkpoint

On 2026-09-12 at 17:43:44 UTC, the user replied: "Works. Continue" after delivery of the Stage-19 test.

- APK: `Meboard-stage19-BaseClearcut-removed-TEST.apk`
- SHA-256 reverified in the build environment: `c06c75a38f61baf442f0ed040d03dcd41cec1c45a528184ae7ca4d3be77611d4`
- Size: 110132140 bytes
- Package: `com.mekromn.meboard`
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`
- Source/report commit: `dcbc67c8cae70fa1d1e03fa967a6e382f1dfc24d`
- Working checkpoint branch: `meboard/working-stage19-20260912`

The user report establishes general working feedback, not an exhaustive feature test or network audit. The installed device APK was not independently read back in this turn. Keep this exact APK as the immediate Stage-20 rollback.

The earlier Stage-16 rollback (SHA-256 `913b5e69997541ad6015d80661677f510826cfd63980b85a9178a95b71780342`) and all previous checkpoint branches remain unchanged. Neither APK is renamed as a newer build or overwritten.

Remaining privacy removals proceed on a separate Stage-20 test branch. No proprietary APK, private signing key, or signing password belongs in this public repository. Privacy-final remains false.
