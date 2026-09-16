# Stage 54g — Meboard UI, About, launcher icon, and default theme

Base: `meboard/stage54f-stock-softkey-icon-resolver-20260915` (user-confirmed working keyboard behavior).

## UI cleanup
- Replace launcher/app icon with the user-supplied round Meboard keyboard artwork.
- Remove `Rate Meboard` from root Settings.
- Remove `Help & feedback` from root Settings.
- Rename `Test Meboard` to `Keyboard test` and give it a dedicated monochrome keyboard icon.
- Replace the inherited About contents with a Meboard-specific page showing the app icon, name, version/build, privacy model summary, and open-source licenses.

## Meboard theme
A real theme package is registered in the standard theme package arrays as `assets:theme_package_metadata_meboard.binarypb`. It uses fixed palette values and is used as the fallback/default only when the existing theme-resolution path does not return an already resolved user theme.

Exact palette:
- background primary `#000000`
- background secondary `#353A42`
- key body `#4B4C4F`
- key hover/pressed `#626366`
- dark key/shadow `#404245`
- primary label `#FFFFFF`
- secondary label `#B7B9C0`
- accent `#147BF6`
- accent pressed/highlight `#3199FE`
- accent contrast/shadow `#075EEA`

Theme assets:
- `assets/theme/theme_package_metadata_meboard.binarypb`
- `assets/theme/style_sheet_meboard.binarypb`
- `assets/theme/style_sheet_meboard_border.binarypb`

## Regression boundary
Compared with decoded Stage 54f, only these classes differ semantically:
- `qyk` — default/fallback theme choice while preserving an already-resolved theme.
- `MeboardTestPreference` — title/icon.
- `MeboardTestPreference$ClickListener` — dialog title.

Stage 54f keyboard behavior (Moonshine return, true incognito, Space long-press, clipboard timeout, SoftKey icon resolver, and prior cleanup) is otherwise untouched.

## Signed candidate
SHA-256: `17c5335cb99e825f53e986e74a9f5fe3f6c45637ff734982247f84d1975ca4ae`

- v3 signature: PASS
- stable signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`
- 16 KiB alignment: PASS
- ZIP integrity: PASS
- fresh Apktool 3.0.3 decode: PASS

Runtime on a real Android device remains the final gate.