# Meboard confirmed-working checkpoint — 20260905T222644Z

The user reported **“It works”** after installing the exact Meboard working reissue.

## Immutable runtime baseline

- APK: `Meboard-WORKING-REISSUE.apk`
- SHA-256: `913b5e69997541ad6015d80661677f510826cfd63980b85a9178a95b71780342`
- Size: `110304172` bytes
- Package: `com.mekromn.meboard`
- Lineage: Stage 16 density-resource repair
- User-confirmed: keyboard renders and Meboard settings open

The installed base APK has not yet been independently re-hashed after this confirmation, so this records a user-confirmed runtime result rather than a device-hash attestation.

## Do not regress this point

Never modify or overwrite this APK in place. Every subsequent removal or repair must be produced on a separate branch and compared against this checkpoint. If a later build breaks keyboard rendering, typing, settings, local AI, language support, or switching, roll back to this exact hash.

## Status boundaries

- Keyboard-rendering baseline: **PASS by user report**
- Settings routing: **PASS by user report**
- Exhaustive feature matrix: **PENDING**
- Idle/ordinary-typing network capture: **PENDING**
- Native monolith privacy completion: **PENDING**
- Privacy-final release: **NO**

## Persistent copies

- GitHub branch: `meboard/checkpoint-working-20260905T222644Z`
- Library: `/Meboard/Checkpoints/20260905T222644Z-confirmed-working`
- Library APK and checkpoint ZIP were materialized back and verified byte-for-byte.
