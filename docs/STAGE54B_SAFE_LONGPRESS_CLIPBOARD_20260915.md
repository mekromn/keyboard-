# Meboard Stage 54b — safe long-press recovery + configurable clipboard retention

Status: **signed test APK; static/build verification PASS; Android runtime smoke gate prepared but not executable in this container because `adb`/Android SDK are absent.**

## Baseline and crash recovery

- Reconstructed from the exact Stage-53 cumulative payload using the guarded Stage-53 replay from confirmed Stage 52.
- Stage 54 and Stage 54a both crashed when the keyboard was shown.
- Stage 54b therefore discards the two keyboard-construction/render hooks introduced by Stage 54:
  - no `mhe` HEADER_MENU ActionDef injection;
  - no `SoftKeyView` post-render icon hook.
- `mhe.smali` SHA-256 remains Stage-53-identical: `9d07ae0798cf72c609b0d5f5a5845ce180a3314dcecd99efeab74c3bbba4c460`.
- `SoftKeyView.smali` SHA-256 remains Stage-53-identical: `f7f6e54cf484d4d5bef8ab4df2ef2f4c1a2cd5d77f8b01fe090bf2f7c2761795`.
- Spacebar and HEADER_MENU long-press handling now lives only inside the existing `pbv` long-press Runnable after it actually fires.
- The custom `pbv` block uses new dedicated `v9/v10` locals (`.locals 11`) rather than reusing stock registers.

## Features in this candidate

1. **Space long-press two-state action**
   - no selection -> Select All;
   - existing selection -> Copy;
   - successful custom action consumes the long-press so release cannot also type Space.

2. **Four-square HEADER_MENU long-press**
   - normal tap remains stock;
   - long-press toggles the live Meboard incognito session and shows an on/off toast.

3. **Clipboard history timeout dropdown**
   - programmatically added to the root Meboard settings page; no settings XML/resource-table rebuild;
   - values: **1 hour, 3 hours, 6 hours, 12 hours, 24 hours**;
   - key: `meboard_clipboard_retention_hours` in normal `com.mekromn.meboard_preferences` storage;
   - default/fallback: **1 hour**;
   - the stock `fjo.a(Context)` (`getUnpinnedItemTimeLimitInMilliSeconds`) is now a single call to `ClipboardRetentionConfig.getMillis(Context)`, so all existing cleanup/query consumers use the chosen timeout;
   - pinned-clip behavior is untouched.

4. **Existing cumulative features preserved**
   - Test Meboard;
   - Moonshine direct long-press voice provider and deferred text commit;
   - Stage-53 privacy/Primes removals.

## Deliberately deferred

The two blank Shift/Emoji icon fallbacks are **not** in Stage 54b. They were part of the crash delta and are being reintroduced separately only after the keyboard-render gate passes. Their normal key actions remain stock; only their missing visual glyphs remain unresolved in this recovery build.

## Signed APK boundary

- APK: `Meboard-stage54b-SAFE-LONGPRESS-CLIPBOARD-TIMEOUT-TEST.apk`
- SHA-256: `d194b59965c291ef959080fc981d7a185382a511606f139f63fb0b15f616d1fe`
- Size: `110267334` bytes
- Non-signature entry set: identical to Stage-53 control (9143 payloads).
- Changed payloads: **classes2.dex**.
- Main `classes.dex`: byte-identical to Stage 53.
- `classes3.dex`, `classes4.dex`, manifest, `resources.arsc`, assets, cleaned settings XML, and all 16 native libraries: byte-identical to Stage 53.
- APK Signature Scheme v3: PASS.
- Permanent Meboard signer certificate preserved.
- 16-KiB ZIP/native alignment: PASS.
- ZIP integrity: PASS.
- Fresh Apktool decode of the signed APK: PASS.

## classes2 semantic delta

- class count: 9504 -> 9508
- added: `com/mekromn/meboard/ClipboardRetentionConfig.smali`, `com/mekromn/meboard/ClipboardTimeoutPreference.smali`, `com/mekromn/meboard/IncognitoToggleAction.smali`, `com/mekromn/meboard/SpacebarSelectionAction.smali`
- deleted: none
- changed survivors: `com/mekromn/meboard/MeboardTestPreference.smali`, `fjo.smali`, `pbv.smali`

## Automated runtime gate

`emulator_smoke_test_meboard.sh` automates the exact failure path:

1. install/update candidate;
2. enable/select Meboard IME;
3. launch Meboard settings;
4. assert `Test Meboard` and `Clipboard history timeout` exist;
5. tap Test Meboard;
6. focus its EditText (forcing keyboard creation/show);
7. assert Meboard process survives and is the shown/current IME;
8. scan logcat for `VerifyError`, `Verifier rejected`, Meboard `FATAL EXCEPTION`, and process crash markers.

A companion `setup_android16_meboard_avd.sh` creates an Android 16 Google APIs AVD for this test. In the current container the smoke run stops before install with `adb is not installed or not on PATH`, so **runtime PASS is not claimed**.
