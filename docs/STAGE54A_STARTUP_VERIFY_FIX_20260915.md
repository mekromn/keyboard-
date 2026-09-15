# Meboard Stage 54a — keyboard-show verifier repair

Status: signed corrective test APK; phone runtime pending.

## Root cause

Stage 54 added the HEADER_MENU long-press incognito action inside `mhe.x()`, which builds `SoftKeyDef` instances during keyboard creation. The patch reused stock register `v2` as a temporary null argument. In the original method, `v2` is the boolean returned by `mhe.F(mic)` and is used immediately afterward as a `Z` argument in stock control flow. This introduced an ART type-flow conflict on the HEADER_MENU path and matches the reported crash when showing the keyboard.

Stage 54a increases `mhe.x()` locals from 8 to 10 and moves the injected action-id/null temporaries to new registers `v8`/`v9`, preserving stock `v1`/`v2`.

## Artifact

- APK: `Meboard-stage54a-STARTUP-VERIFY-FIX-TEST.apk`
- SHA-256: `c374eae9f244561c9ba54b78481243de1cea16ef8a2bd4c596b745182832e501`
- Signature: Meboard permanent v3 signer
- 16 KiB native alignment: PASS

## Exact boundary

Stage54 -> Stage54a changes exactly `classes.dex`. All other non-signature payloads are byte-identical. Space Select-All/Copy, HEADER_MENU incognito long-press, Shift/Emoji visual fallback, Moonshine, Test Meboard, and prior cleanup state are retained.
