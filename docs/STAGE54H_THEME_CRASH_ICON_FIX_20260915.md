# Meboard Stage 54h verification

Base: Stage 54g, with Stage 54f still the last user-confirmed fully working keyboard-behavior base.

## User-reported regressions fixed

### 1. Settings > Theme crash
Root cause found: `assets/theme/theme_package_metadata_meboard.binarypb` in Stage 54g was malformed protobuf. The main Meboard stylesheet parsed, but the package metadata did not; opening the Themes UI attempts to enumerate/parse theme packages, so this was a direct crash vector.

Stage 54h rebuilds the metadata using the exact field topology of stock `theme_package_metadata_google_blue_dark.binarypb`:
- repeated field 2 stylesheet names
- field 3 border-mode submessage
- stock color-common / non-dynamic / color-rules / Google-blue-rules chain retained
- Meboard main and border sheets substituted only at their normal sheet slots

The previous zero-byte `style_sheet_meboard_border.binarypb` is also replaced with a valid protobuf stylesheet containing Meboard's exact background/key colors.

Fresh signed-APK decode confirms all three custom theme protobufs parse structurally:
- `theme_package_metadata_meboard.binarypb`: 261 bytes, valid protobuf
- `style_sheet_meboard.binarypb`: 1393 bytes, valid protobuf
- `style_sheet_meboard_border.binarypb`: 332 bytes, valid protobuf

Exact Meboard palette remains:
- `#000000` background
- `#353A42` secondary background
- `#4B4C4F` key body
- `#626366` key highlight/pressed
- `#404245` dark/shadow
- `#FFFFFF` primary legend
- `#B7B9C0` secondary legend
- `#147BF6` accent blue
- `#3199FE` blue highlight/pressed
- `#075EEA` blue contrast/shadow

### 2. New launcher icon not appearing
The Stage 54g adaptive foreground bitmap itself contained rendering artifacts outside the circular artwork. Stage 54h regenerates the icon directly from the user's original transparent PNG.

To avoid adaptive-foreground safe-zone scaling, the actual artwork is carried in the adaptive **background** layer; the foreground layer is transparent. The monochrome layer remains available through the adaptive-icon XML.

All density resources were regenerated at the stock adaptive-icon sizes: mdpi 108x108, hdpi 162x162, xhdpi 216x216, xxhdpi 324x324, xxxhdpi 432x432.

Stage 54h also bumps versionCode from `175940518` to `175940519` and versionName to `18.0.3.954559732-meboard54h` so package managers/launchers have a clear cache invalidation signal.

## Regression boundary
Compared with Stage 54g, no DEX entry changed. The Stage 54g theme-selection hook and all Stage 54f keyboard behavior remain byte-identical in code.

Working behavior intentionally untouched: Moonshine return, Space long-press Select All/Copy, true incognito + native icon, Clipboard timeout, Keyboard test, Stage 54f SoftKey resolver, and all prior cleanup.

## Signing/package gates
- package: `com.mekromn.meboard`
- versionCode: `175940519`
- APK size: 110,516,009 bytes
- SHA-256: `a6c33fe7e872d8fdecb2cd89d43652b2b6a067124488003632216d924c21d38d`
- APK Signature Scheme v3: PASS
- signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`
- 16-KiB ZIP alignment: PASS
- ZIP integrity: PASS
- fresh Apktool 3.0.3 decode: PASS
