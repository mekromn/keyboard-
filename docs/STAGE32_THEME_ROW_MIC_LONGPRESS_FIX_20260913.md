# Meboard Stage 32 — Theme row + toolbar mic long-press fix

Status: signed test APK; static/build checks PASS; phone runtime pending; privacy-final NO.

## User-observed Stage31b failure
Stage31b launches, but the AMOLED background choice is not visible and mic long-press does not open the provider chooser.

## Root causes
1. The stock **Key borders** switch (`0x7f0b2a54`) is inside a horizontal `LinearLayout`. Stage31 inserted the new `RadioGroup` immediately after the switch inside that horizontal row, placing the new controls to the right/off-screen. Stage32 inserts the radio group after the entire Key-borders row in its vertical parent.
2. The toolbar voice widget is constructed by `myy` with role `mif.i` (`WIDGET_VOICE_KEY`) and view ID `0x7f0b2b26`. Gboard installs the `SoftKeyView` touch/click/long-click/focus listeners through `SoftKeyView.n(Lsuz;)`. Stage31 intercepted `SoftKeyboardView.onLongClick()`, which does not own every toolbar-mic long press. Stage32 wraps only the stock long-click listener at `SoftKeyView.n(...)`.

## Theme behavior
The existing Theme-details presenter call to `MeboardThemeMode.install(...)` is retained. The two choices are:
- Theme background
- AMOLED black glass keyboard background

They are mutually exclusive. Apply persists the selection in private Meboard preferences (`meboard_custom`, key `meboard_amoled_black_glass`). The AMOLED renderer changes only tagged `keyboard-body-area` backgrounds to true #000000 with rounded corners and a subtle edge, and restores the original theme drawable when disabled. There is no whole-window blur/dimming.

## Mic behavior
`SoftKeyView.n(Lsuz;)` still installs the original stock `Lsuz` as OnTouchListener, OnClickListener and OnFocusChangeListener. Only OnLongClickListener is wrapped by new `VoiceLongClickProxy`. The proxy handles the exact toolbar voice-key ID `0x7f0b2b26` (plus the existing role-marker fallback); every non-voice long press delegates to the original listener. Normal mic tap therefore remains on the stock click path.

## Safety cleanup
The Stage31 onStartInput glass hook is removed. `oup` is byte-identical to Stage30. The Stage31 SoftKeyboardView attach/long-click hooks are removed; `SoftKeyboardView` is byte-identical to Stage30. `InputView` is unchanged from Stage31b.

## Artifact facts
- APK: `Meboard-stage32-THEME-ROW-MIC-LONGPRESS-FIX-TEST.apk`
- SHA-256: `4c533d06a93724538b4423e61b9b8fea99858eab8cd5be29dfd57e0d913aae29`
- Size: 110111660 bytes
- Package: `com.mekromn.meboard`
- Signer cert SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`
- Stage31b base SHA-256: `7646b98b9f59d2b94c7fd20e9c6903f93dae5a6b27ef6221122e235e534f5232`

Decoded-code delta vs Stage31b: 21750 -> 21751 classes, one added class (`VoiceLongClickProxy`), zero deletions, six modified existing classes (`oup`, `SoftKeyboardView`, `SoftKeyView`, `MeboardGlass`, `MeboardThemeMode`, `VoiceProviderChooser`). Every other class is byte-identical.

APK payload set remains 9148 non-signature entries. Only `classes.dex` changed. Manifest, `resources.arsc`, DEX 2-4, all resources/assets and all 16 native libraries are byte-identical to Stage31b. New main DEX SHA-256: `be39fba06cd365ee7627c5d6baa12095b0cd6367cf69529aa6ea834233909c3b`.

Checks: ZIP CRC PASS, APK v3 signature PASS with permanent signer, 16 KiB alignment PASS, all DEX header checks PASS, fresh Apktool 3.0.3 decode of the signed APK PASS with no missing-resource warnings. A clean Stage31b-tree replay of the guarded patch produced a byte-identical Stage32 main DEX.

## Runtime gate
Do not promote until phone confirms: launch; radio choices visible directly below Key borders; AMOLED Apply changes actual keyboard background only; Theme background restores normal theme; normal mic tap works; mic long-press opens chooser; alternate-provider recognition is tested separately.
