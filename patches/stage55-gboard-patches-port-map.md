# Stage55 port map

## Main DEX
- `nxw.g()` -> passes stock flag results through `MeboardFlagForce.apply(name, result)`.
- `qyd` -> `more_pill_keys` default gate TRUE.
- `rqx` -> `enable_use_bluetooth_setting` default gate TRUE.
- `ilq` -> Hyperspeed flags enabled and supported language tags `*`.
- `AccessPointsBar` -> live count from `TopToolbarConfig`.

## DEX2
- `iof.j(pnu)` -> maps positive text keys to Flow Mode typing-pulse `-10043`, preserving control keys.
- `PreferencesSettingsFragment.aC()` -> `TopToolbarPreference`.
- `ClipboardSettingsFragment.aC()` -> existing retention control + `ClipboardEnhancementPreferences`.
- `ClipboardKeyboard.l()` -> configurable 1/2/3 grid columns.
- `fjk.F()` -> configurable clipboard item limit.
- `fjk.p()` -> configurable card preview/labels/index/1,000-character cap.

## Added Meboard classes
- `MeboardFlagForce`
- `TopToolbarConfig`
- `TopToolbarPreference`
- `ClipboardEnhancementConfig`
- `ClipboardEnhancementPreferences`
- `ClipboardCardEnhancer`

No external `dev.jason.gboardpatches` runtime/framework classes are bundled; only the requested behavior is ported into Meboard-native seams for the exact 18.0.3 target.