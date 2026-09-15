# Meboard Stage 54 — Space Select/Copy, Incognito Hold, and Blank Key Icon Repair

Status: **signed test APK; static/build verification PASS; phone runtime pending**.

## Artifact

- APK: `Meboard-stage54-SPACE-SELECT-COPY-INCOGNITO-BLANK-KEY-FIXES-TEST.apk`
- SHA-256: `c3a7bb7765944dbfbbf6d722d5e1d0ccb130ab3c5e61557c09f91925c363433f`
- Package: `com.mekromn.meboard`
- Version code: `175940518`
- Version name: `18.0.3.954559732-release-arm64-v8a`
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`
- Input: Stage 53 `Meboard-stage53-PRIMES-MEMORY-CAPTURE-REMOVED-TEST.apk`

Stage 52 was the last phone-confirmed cleanup APK before the Stage-53 memory-capture removal. This Stage-54 test carries the Stage-53 removal forward and adds the requested interaction/icon changes; passing the phone test therefore validates the combined cumulative line.

## Feature 1 — Spacebar long-press two-state action

The existing Gboard long-press runnable `pbv` is extended only for the actual Space action (`pnu.c == 0x3e`).

- No selected text: `InputConnection.performContextMenuAction(android.R.id.selectAll)`.
- Existing selection: `InputConnection.performContextMenuAction(android.R.id.copy)`.
- A successful action consumes the active key gesture through the existing `pvi.C()` path, preventing release from also inserting Space.
- Ordinary short-tap Space and every non-Space long-press fall through to stock behavior.

New helper: `com.mekromn.meboard.SpacebarSelectionAction`.

## Feature 2 — long-press four-square toolbar key toggles incognito

The marked four-square key is the stock access-point role `mif.d = HEADER_MENU`.

Stage 54 adds a LONG_PRESS ActionDef only to that role. The normal PRESS ActionDef is not replaced or redirected.

The runnable toggles Gboard/Meboard's current `InputSessionNotification` incognito state (`owq.f()`), mirrors the state into the active EditorInfo `IME_FLAG_NO_PERSONALIZED_LEARNING` bit, and republishes through stock `owq.e(...)` notification dispatch. A toast reports `Incognito mode on` / `Incognito mode off`.

New helpers:
- `com.mekromn.meboard.IncognitoToggleAction`
- `com.mekromn.meboard.IncognitoToggleActionRunnable`

This is a session toggle; runtime testing is required to verify every UI/learning consumer reacts immediately in the installed build.

## Feature 3 — blank Shift and Emoji key icons

Screenshot review showed the two blank keys are:

1. the Shift/Caps key in the alphabet layout;
2. the Emoji key in the symbols layout.

They are not toolbar slots. The earlier generic toolbar-placeholder experiment was discarded and is **not present** in this APK.

`SoftKeyView` gets one visual-only post-render hook. It does nothing if the stock primary icon drawable exists. If the icon is genuinely absent, it checks the key's accessibility content description and restores a small built-in drawable only for Shift/Caps or Emoji. Existing tap/long-press ActionDefs are not changed.

New helpers:
- `com.mekromn.meboard.BlankKeyIconFix`
- `com.mekromn.meboard.BlankKeyIconDrawable`

No resource-table rebuild or new drawable resource is used.

## Signed-output preservation proof

Relative to Stage 53, non-signature payload names are identical. Exactly two payloads change:

- `classes.dex`
- `classes2.dex`

Everything else is byte-identical, including:

- `classes3.dex`, `classes4.dex`
- `AndroidManifest.xml`
- `resources.arsc`
- privacy/settings XML payloads
- assets
- all native libraries

Fresh decode class delta:

### Main DEX
- 7,451 → 7,455 classes
- added: `BlankKeyIconDrawable`, `BlankKeyIconFix`, `IncognitoToggleAction`, `IncognitoToggleActionRunnable`
- changed stock classes: exactly `mhe`, `SoftKeyView`
- deleted: none

### DEX 2
- 9,504 → 9,505 classes
- added: `SpacebarSelectionAction`
- changed stock class: exactly `pbv`
- deleted: none

### DEX 3 / DEX 4
- class counts and every decoded class are byte-identical.

The old generic `ToolbarFallbackIcon` / `ToolbarFallbackDrawable` experiment is absent.

## Locked cumulative gates

- Moonshine preferred package `org.futo.voiceinput.moonshine` remains present.
- `VoiceProviderRelayActivity` and `VoiceProviderChooser` are byte-identical to Stage 53.
- `Test Meboard` helper classes remain present.
- Stage-53 deleted descriptors `Luct;` and `Lucq;` remain absent.
- `VoiceDonationManager`, `maybeAddDonationRequest`, `psa`, `psp`, `mck`, `mcj`, and `NetworkMetricServiceImpl` remain absent by their locked descriptor/implementation gates.
- APK Signature Scheme v3: PASS; v1/v2/v4 disabled.
- 16-KiB native ZIP alignment: PASS.
- Permanent Meboard signing certificate preserved.

## Runtime acceptance

Install directly over the current same-signer Meboard without clearing data and test:

1. Ordinary typing and normal Space tap.
2. With no selection, hold Space: entire editor text becomes selected and no Space is inserted on release.
3. Hold Space again while text is selected: current selection is copied; selection remains.
4. Normal tap the four-square toolbar key: stock menu behavior remains.
5. Long-press the four-square key: incognito toggles and a confirmation toast appears; long-press again toggles it off.
6. Alphabet layout: Shift key now has a visible Shift glyph and still shifts/caps normally.
7. Symbols layout: Emoji key now has a visible smiley glyph and still opens Emoji normally.
8. Short mic tap remains stock Meboard dictation.
9. Long mic press still launches Moonshine and returned text is committed.
10. `Test Meboard` still opens/focuses correctly.
