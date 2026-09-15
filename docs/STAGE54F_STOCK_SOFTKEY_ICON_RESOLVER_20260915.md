# Meboard Stage 54f verification

## Purpose
Stage 54e is the user-confirmed working baseline except that two special-key icons remain blank. Stage 54f changes only the stock special-key icon resolution fallback inside `SoftKeyView`.

## Root cause addressed
The affected keyboard XMLs supply theme attribute resource IDs for several stock icons. In Meboard, the attribute integer can be nonzero while the later `rqi.g(Context, resourceId)` theme/resource resolver returns `0`. The stock renderer then has no usable drawable and the key appears blank.

Stage 54f leaves the normal renderer untouched when resolution succeeds. Only when the icon value is already `0` or `rqi.g(...)` resolves to `0`, it uses the current logical `SoftKeyDef.d` ID to substitute the exact stock Gboard drawable and then continues through Gboard's existing `Logo.s(resourceId, true)` renderer.

## Exact fallback mappings
- Shift off: softkeys `0x7f0b0897`, `0x7f0b2116`, `0x7f0b245e`, `0x7f0b2463`, `0x7f0b2464` -> stock `0x7f0805fc`
- Shift on: `0x7f0b0898`, `0x7f0b2465`, `0x7f0b2466`, `0x7f0b2467`, `0x7f0b2468`, `0x7f0b2469` -> stock `0x7f0805fd`
- Shift/caps locked: `0x7f0b2117`, `0x7f0b2460`, `0x7f0b2462` -> stock `0x7f0805fb`
- Stock keyboard/symbol switch: `0x7f0b2250` -> stock `0x7f0805eb`
- Stock space icon variants: `0x7f0b24d5`, `0x7f0b24d7`, `0x7f0b24d9` -> stock `0x7f080600`
- Stock clipboard-state keys: `0x7f0b22a7` -> `0x7f08056e`; `0x7f0b22a8` -> `0x7f08056f`

## Stock asset provenance
All seven fallback WebP resources in the final Meboard APK are byte-identical to the same resource IDs in the user's unmodified Gboard 18.0.3 xxhdpi split.

## Payload delta vs Stage 54e
- Non-signature entries: 9143 -> 9143
- Missing entries: 0
- Extra entries: 0
- Changed entries: exactly 1 (`classes.dex`)
- Fresh smali comparison of main DEX: exactly 1 changed class: `com/google/android/libraries/inputmethod/widgets/SoftKeyView.smali`
- `classes2.dex`, `classes3.dex`, `classes4.dex`, resources, manifest, assets and native libraries are byte-identical to Stage 54e.
- Therefore Stage 54e's working Moonshine immediate-return behavior, true-incognito toggle/icon, Space hold Select All/Copy, Clipboard timeout dropdown, Moonshine provider, Test Meboard and prior cleanup are preserved.

## Build verification
- Main DEX assembly: PASS (7452 classes, API 28 / DEX 039 path used by prior stages)
- Fresh Apktool 3.0.3 decode: PASS
- ZIP integrity: PASS
- zipalign `-c -P 16 4`: PASS
- APK Signature Scheme v3: PASS
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

## Artifact
- Filename: `Meboard-stage54f-STOCK-SOFTKEY-ICON-RESOLVER-FIX-TEST.apk`
- SHA-256: `e945f6f7e9c52b3addd8099338c136a938f353523305d843291e2df92662f1bf`

## Runtime note
This environment has no connected Android/ADB runtime, so the decisive runtime gate remains the user's device test. Stage 54e remains the rollback baseline until Stage 54f is confirmed.
