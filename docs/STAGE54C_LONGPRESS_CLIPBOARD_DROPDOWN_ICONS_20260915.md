# Meboard Stage 54c — live long-press routing, Clipboard dropdown, safe blank-key glyphs

Status: signed test candidate. Static/build gates pass; Android runtime smoke gate exists but cannot be executed in the current container because `adb`/Android SDK are absent.

## Fixes relative to Stage 54b

### Space and four-square long press

Stage 54b put the actions inside the existing `pbv` long-press runnable, but stock `pvi` only scheduled that runnable when a key already had a `LONG_PRESS` ActionDef. Space and the active HEADER_MENU key did not reliably advertise one, so the branch never ran.

Stage 54c fixes the stock gesture-engine eligibility instead of attaching a generic View listener:

- `CustomLongPressKeys.type(pvi)` identifies Space from the stock press action code `0x3e` and HEADER_MENU from view ID `0x7f0b053e` (`key_pos_header_access_points_menu`).
- `pvi.ad(ActionDef)` treats only those keys as long-press capable.
- `pvi.y()` schedules the existing stock long-press runnable for them.
- The timeout remains stock `pvi.R(SoftKeyDef)`, so it is still clamped to Gboard/Meboard's normal long-press delay.
- `pbv` selector 19 dispatches Space to `SpacebarSelectionAction` and HEADER_MENU to `IncognitoToggleAction`, then consumes the gesture through `pvi.C()` on success.

Space: no selection => Select All; selected text => Copy. HEADER_MENU normal tap stays stock; hold toggles the live incognito/no-personalized-learning session and shows a toast.

### Clipboard history timeout

The Stage 54b root-page injection is removed. The preference is now injected by `ClipboardSettingsFragment.aC()`, the normal post-inflation extension point, so it appears under **Settings -> Clipboard**.

It is a real AndroidX `DropDownPreference` with:

- 1 hour
- 3 hours
- 6 hours
- 12 hours
- 24 hours

The key remains `meboard_clipboard_retention_hours`, so a value already selected in 54b is preserved. A `ClipboardTimeoutSummaryProvider` displays `Current: <selected value>` under the row. Default/fallback remains 1 hour.

The actual unpinned-clip timeout source remains `fjo.a(Context)` -> `ClipboardRetentionConfig.getMillis(Context)`, so the selection controls all existing cleanup/query consumers. Pinned clips are untouched.

### Blank Shift / Emoji keys

The previous custom Drawable renderer is discarded. Stage 54c uses only a visual fallback at the end of `SoftKeyView.x(SoftKeyDef)`:

- Shift IDs `0x7f0b0603` / `0x7f0b0604`;
- Emoji IDs `0x7f0b0608` / `0x7f0b060a`;
- if the stock image child already has a drawable, do nothing;
- only when genuinely blank, show `⇧` or `☺` in the key's existing text child.

No new drawable resources, Canvas code, resource-table rebuild, or action changes are used.

## Verification

Signed APK: `Meboard-stage54c-LONGPRESS-CLIPBOARD-DROPDOWN-ICONS-FIX-TEST.apk`

SHA-256: `c84b1f07b8b99d9ecc654d7e6183fd4e8283357ac57f062afbd64aea75f508ce`

Size: 110267355 bytes.

Stage 54b -> 54c changes only `classes.dex` and `classes2.dex`; the non-signature ZIP entry set remains exactly 9,143 entries with none added/deleted. DEX 3/4, manifest, `resources.arsc`, assets, settings/privacy XML, and all 16 native libraries are byte-identical.

Main DEX remains 7,451 classes; only `SoftKeyView` changes. DEX2 goes 9,508 -> 9,510 classes, adding only `ClipboardTimeoutSummaryProvider` and `CustomLongPressKeys`; changed survivors are `ClipboardSettingsFragment`, `ClipboardTimeoutPreference`, `IncognitoToggleAction`, `MeboardTestPreference`, `SpacebarSelectionAction`, `pbv`, and `pvi`.

Fresh Apktool decode passes. APK v3 signature, permanent Meboard signer, ZIP integrity, and 16-KiB native alignment pass. Moonshine/Test Meboard remain present and all locked Stage-53 privacy/Primes removals remain absent.

## Runtime promotion gate

`tools/emulator_smoke_test_meboard.sh` now verifies the exact keyboard-show crash repro plus the settings placement/UI regression: Test Meboard must render the IME without a fatal/verifier crash; Clipboard timeout must be absent from root settings, present in the Clipboard submenu, show a `Current:` value, and expose all five dropdown options.

The current environment has no `adb`, so runtime PASS is deliberately not claimed until this APK is tested on Android.
