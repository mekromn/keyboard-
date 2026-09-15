# Meboard Stage 54d — true native incognito + native status icon + key icon repair

Status: **signed test APK; static/build verification PASS; user runtime test pending**.

## Base

Stage 54d is cumulative from the user-confirmed-working Stage 54c. Stage 54c's clipboard timeout dropdown, Space long-press Select All/Copy behavior, HEADER_MENU long-press scheduling, Moonshine voice integration, Test Meboard, and prior privacy/removal gates are preserved.

## True incognito behavior

The 4-square long-press now drives Gboard's own runtime incognito/learning contract rather than a parallel cosmetic flag.

The toggle:

1. obtains the live InputMethodService;
2. sets/clears Android `IME_FLAG_NO_PERSONALIZED_LEARNING` (`0x01000000`) on the current and stored EditorInfo objects;
3. invokes `Look.i()` / `InputBundle.reactivateIme`;
4. native reactivation calls each active IME's `onActivate(EditorInfo, incognitoMode, keyboardType)` using `Looh.G()`;
5. `Leqy.G()` derives incognito from the same no-personalized-learning flag;
6. `AbstractIme.onActivate` stores the incognito boolean in `H` and recomputes learning field `M`; its learning predicate returns false whenever `H` is true;
7. the normal InputSessionNotification is then published so other native consumers update to the same state.

## Native header status icon

No custom incognito icon is drawn. Gboard already packages a dedicated HEADER_MENU incognito SoftKeyDef in `mlr.c` using drawable `0x7f080715` (the stock hat/glasses vector). Stage54d adds `mlq.hn(...)` so normal input-view session updates delegate to the existing `mlq.d(...)` switcher. Incognito on swaps the 4-square header to the stock incognito definition; off swaps it back.

The Stage54c toast is completely removed.

## Shift / Emoji blank-key repair

Stage54c's label fallback did not render on the user's active key views. Stage54d targets the actual key ImageView child and uses packaged native vectors:

- Shift key IDs `0x7f0b0603` / `0x7f0b0604` -> drawable `0x7f08071a`
- Emoji/emoticon key IDs `0x7f0b0608` / `0x7f0b060a` -> drawable `0x7f0803f7`

No resource-table rebuild or new drawable is introduced. Existing key actions are untouched.

## Exact Stage54c -> Stage54d boundary

Non-signature entry set remains 9143 entries. Exactly two APK payloads change: `classes.dex` and `classes2.dex`.

Byte-identical to Stage54c: `classes3.dex`, `classes4.dex`, AndroidManifest.xml, resources.arsc, assets, cleaned settings/privacy XML, and all 16 native libraries.

Fresh signed decode:

- main DEX: 7451 -> 7451 classes; changed only `mlq` and `SoftKeyView`; no additions/deletions.
- DEX2: 9510 -> 9510 classes; changed only `IncognitoToggleAction`; no additions/deletions.
- DEX3/4: byte-identical.
- `mlr`, `Lowq`, Stage54c `pbv`, clipboard retention resolver/dropdown, and Moonshine helpers are unmodified.

## Signed artifact

- APK: `Meboard-stage54d-TRUE-INCOGNITO-NATIVE-ICON-KEY-ICONS-TEST.apk`
- SHA-256: `dad5cb2814d8bc6fc2e1cb43d50dc11af11523e6bb17fdb718fdee16456cc57d`
- Size: 110267355 bytes
- ZIP integrity: PASS
- Apktool 3.0.3 fresh signed decode: PASS
- DEX format: 039, API 28 assembly
- APK Signature Scheme v3: PASS; v1/v2/v4 disabled
- signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`
- 16-KiB alignment: PASS

## Static semantic gates

PASS: native reactivation present; session publish present; toast absent; `mlq.hn` delegates to native `mlq.d`; native `mlr.c` icon `0x7f080715` remains; Shift/Emoji native vector IDs present; Stage54c Space/Clipboard/Moonshine paths preserved; prior locked removals remain absent.

Runtime PASS is not claimed because the build environment has no connected Android device/ADB. On-device gate: Test Meboard render; toggle 4-square and verify no toast/native hat-glasses icon on and normal icon off; verify incognito-session input is not learned; verify Shift and Emoji icons/actions; recheck Space, Clipboard timeout, Moonshine, and Test Meboard.
