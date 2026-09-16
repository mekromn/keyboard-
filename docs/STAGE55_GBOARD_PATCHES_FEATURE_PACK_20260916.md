# Meboard Stage 55 — Gboard-patches feature pack

Base: Stage54n.

Upstream feature reference: `jasonwu1994/Gboard-patches` commit `ca0ebe6e36f19cad382ef70f6ae783c770917263`, matching Gboard `18.0.3.954559732-release-arm64-v8a`.

## Ported features

- **Key Shape Selection**: unlocks stock Theme details > Key shape via `more_pill_keys`, without forcing a shape.
- **Use Bluetooth microphone**: unlocks the stock Voice typing setting via `enable_use_bluetooth_setting`.
- **Hyperspeed typing animation**: opt-in Meboard preference; enables the stock Flow Mode flags for all keyboards and maps eligible positive text key codes to stock pulse code `-10043` in `iof.j(pnu)`.
- **Top toolbar item count**: opt-in override with values 3–8; applies to `config_max_access_points` and `config_default_access_points_num_on_bar` only when enabled.
- **Clipboard enhancements**: extended retention (through 7/30 days), item limit, preview lines, countdown, creation time, order index + direction, 1/2/3 columns, and optional first-1,000-character card rendering.

## Preservation boundary

Only `AndroidManifest.xml`, `classes.dex`, and `classes2.dex` differ from Stage54n. `resources.arsc`, DEX 3/4, Meboard theme assets, stock assets, and native libraries remain byte-identical.

Final APK SHA-256: `52542527ba09ad1c53af13fa953200db008e67af88e7deea9b87179822f07daf`.

Runtime testing remains device-gated; this checkpoint records the statically verified test build, not a runtime acceptance claim.
