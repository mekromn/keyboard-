# Meboard Stage 31 — AMOLED Theme background radio + stock mic long-press fix

Status: **signed test build; static/build checks pass; phone runtime pending; privacy-final NO**.

## Artifact identity

- APK: `Meboard-stage31-AMOLED-ThemeRadio-VoiceLongPress-FIX-TEST.apk`
- SHA-256: `cd033a4945f5654c37a50eece58e2b4a296c201168b4ddaa1c8c6091f9b44504`
- Size: 110111660 bytes
- Package: `com.mekromn.meboard`
- Version code: `175940518`
- Permanent signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`
- APK Signature Scheme v3 verified.
- Stage 27 remains the last user-confirmed broadly working rollback. Stage 30 is not promoted.

## Why the Stage-30 microphone hook failed

`SoftKeyView.n(Lsuz;)` installs Gboard's stock `OnTouchListener`, `OnClickListener`, and `OnLongClickListener` after the Stage-30 custom listener. That overwrote the custom long-press hook.

Stage 31 removes the failed touch-listener/posted-runnable classes. `mhe.J(SoftKeyView,mic)`, the actual access-point binding path, marks only a view bound as `mif.i` (`WIDGET_VOICE_KEY`). `SoftKeyboardView.onLongClick(View)` then checks that mark at the real stock long-click dispatcher. If the view is the voice key, the provider chooser is shown; otherwise execution falls through to the original long-click implementation. After stripping the single Stage-31 interception prefix, the stock method is exact against Stage 30.

`mic.smali` is byte-identical to user-confirmed Stage 27, including the normal mic click route. The checked core voice classes `kgm`, `kgw`, `kht`, `kjp`, `kjm`, `kig`, `fct`, `ruo`, and `rrf` are also byte-identical to Stage 27.

The chooser contains `Meboard standard voice typing` and installed services visible for `android.speech.RecognitionService`. External-provider selection is one-shot and does not replace normal-tap Meboard dictation.

## AMOLED Black Glass placement and behavior

The Stage-30 Preferences switch is gone. Theme details now receives a two-choice radio group directly below stock **Key borders** (`0x7f0b2a54`):

1. `Theme background`
2. `AMOLED black glass keyboard background`

The two options are mutually exclusive background modes. The selected theme continues to provide key colors/shapes/labels while AMOLED mode overrides only the keyboard body background. Existing Theme **Apply** commits the pending mode; existing **Cancel** discards it.

AMOLED rendering targets only actual views tagged `keyboard-body-area`, uses a true `#000000` base, 16 dp rounding and a subtle translucent glass edge. It never applies a whole-IME-window blur or dim. The renderer caches the selected theme's current background drawable and restores it when `Theme background` is selected; if the selected theme repaints while AMOLED mode is active, the newest theme drawable becomes the restoration target.

No `FLAG_BLUR_BEHIND`, `setBackgroundBlurRadius`, or `setBlurBehindRadius` is used by this path. This intentionally prevents the Stage-29 full-screen blurred/dark slab. No claim of real backdrop blur behind the IME is made.

## Payload preservation

Versus Stage 30, all 9148 non-signature entry names are preserved. Exactly three decompressed payloads change:

- `classes.dex`
- `classes2.dex`
- `res/xml/setting_preferences.xml`

The other **9145 entries are byte-identical**, including `resources.arsc`, `AndroidManifest.xml`, all launcher/mipmap icon payloads and all 16 native libraries. A fresh decode of the signed APK completed without missing-resource warnings. `aapt2 dump badging` resolves the application label to `Meboard` and the launcher icon to `res/mipmap-anydpi-v21/ic_app.xml`.

Class count remains 21750. Stage 31 adds `MeboardThemeMode` and its radio listener and removes the failed Stage-30 `VoiceProviderChooser$TouchListener` and `$ShowRunnable`.

## Privacy boundary

The three sharing rows remain absent from `setting_privacy.xml`, and the direct `VoiceDonationManager` descriptor / `maybeAddDonationRequest` marker remains absent. Local personalization and learned-data deletion controls remain.

Because `resources.arsc` is intentionally preserved to avoid another resource-table regression, the obsolete preference-key strings `enable_user_metrics`, `user_enable_federated_training`, and `enable_voice_donation` each still occur once in the resource table. This is a known remaining physical-cleanup item. Privacy removal remains incomplete.

## Phone acceptance gate

1. Verify cold launch and normal app icon.
2. Theme details: verify the two background radio choices appear directly below Key borders.
3. Select AMOLED Black Glass and Apply. Only the keyboard body should become black/glass; the app above it must remain untouched.
4. Select Theme background and Apply. The selected theme background should return.
5. Normal microphone tap must use stock Meboard voice typing.
6. Long-press microphone must open the provider chooser; cancelling must not start recording.

The historical intermittent first-word dictation cutoff remains open/currently nonreproducible; Stage 31 does not claim to fix it.
