# Meboard Stage 54m

Cumulative continuation from the Stage 54k line.

## Additions

- Adds a separately selectable `Meboard Transparent` theme.
  - It keeps the corrected Meboard palette and action-key contrast behavior.
  - The only base-theme color difference is `default_keyboard_background_primary_color`: Meboard uses `#FF000000`; Meboard Transparent uses `#B1000000`.
- Adds `Voice typing sounds` under Voice typing settings.
  - Key: `meboard_voice_typing_sounds`.
  - Default: enabled.
  - OFF gates the central Meboard/Gboard `VoiceSoundManager` sound path without disabling dictation.
- Adds Emoji-key long press to toggle the existing `enable_vibrate_on_keypress` preference.
  - Emoji/smiley key IDs: `0x7f0b060a` and `0x7f0b0608`.
  - The same stock long-press timer used by existing Stage 54 custom long presses schedules this action.
  - The hold gives one Android long-press haptic acknowledgement, then toggles the stock vibration preference.
  - Normal Emoji tap remains unchanged.

## Artifact identity

- package: `com.mekromn.meboard`
- versionCode: `175940523`
- versionName: `18.0.3.954559732-meboard54m`
- permanent signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`
- signed APK SHA-256: `0d39e9585c92770677c88321a179677ef49ae611fbdf75251f656305aceb5a5d`

Static verification passes fresh decode, ZIP integrity, 16-KiB alignment, and APK Signature Scheme v3. Runtime acceptance remains device-gated.