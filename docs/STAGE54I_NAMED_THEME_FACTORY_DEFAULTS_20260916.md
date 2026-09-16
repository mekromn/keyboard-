# Meboard Stage 54i — named theme + fresh-install factory profile

Stage 54i continues from Stage 54h.

## Theme catalog repair

The custom Meboard package is moved out of the unlabeled Colors swatch grid and registered as a labeled built-in tile in the **Default** theme section:

```xml
<item>assets:theme_package_metadata_meboard.binarypb</item>
<item>Meboard</item>
```

The Stage 54h theme metadata/base/border protobuf repair remains intact.

## Fresh-install-only factory profile

`MeboardFactoryDefaults.apply(Context)` is called from `LatinApp.e()`.

The helper applies the screenshot-derived profile only when:

- `PackageInfo.firstInstallTime == PackageInfo.lastUpdateTime`; and
- `meboard_factory_defaults_v1_applied` is false.

It therefore does not reset an existing installation during an APK update.

The profile seeds the requested layout/correction/glide/clipboard/emoji/voice values, a 24-hour unpinned clipboard timeout, and this toolbar order:

```text
clipboard;translate;textediting;settings;theme_setting;one_handed;floating_keyboard;gif_search;sticker;share;search
```

The same order is used for the stock `access_points_order` and `access_points_order_for_new_user_on_phone` defaults.

## Artifact

- package: `com.mekromn.meboard`
- versionCode: `175940520`
- versionName: `18.0.3.954559732-meboard54i`
- APK SHA-256: `fc39907afab8d4edf7fcad24c45ff4d5fab6b63473c5caa27f8907beefeb708b`
- permanent signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`
- APK Signature Scheme v3: PASS
- ZIP integrity: PASS
- 16-KiB alignment: PASS

Compared with the intermediate named-theme-only Stage 54i candidate, the factory-profile addition changes only `classes.dex`.

Runtime device acceptance remains required.