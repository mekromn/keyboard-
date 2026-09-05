# Meboard keyboard split-resource ID repair — 2026-09-05

After the `LatinApp.e()` Context-register repair, `LatinIME` bound but crashed
while loading its keyboard definition:

```text
AssertionError: Failed to fetch keyboard for prime when activating
Caused by: IllegalStateException: Failed to get identifier from name: 0
```

The xxhdpi split's files had been fused into the standalone APK without merging
all of its `public.xml` declarations. AAPT reassigned those resources while
keyboard XML retained unresolved null references. At runtime one required
attribute was interpreted as the resource name `0`.

The complete repair merges **114** original split resource IDs and restores
**194** lost references across **48 XML files**, including split `values`
resources as well as file-backed drawables. The compiled gate verifies the
original IDs and rejects null, numeric-zero, or name-`0` resource values.

All four DEX files and all 16 native libraries in the promoted candidate are
byte-identical to the previous build that reached IME startup. This repair is
resource-only: it does not restore telemetry/account/certificate-whitelist code
or remove any user-facing feature.

Persistent artifacts and one-file continuation state are in:

```text
/Meboard/Checkpoints/20260905T133500Z
```

Runtime acceptance remains pending: install exact candidate, verify installed
SHA-256, bind, render, type, switch away, and switch back before advancing deeper
privacy removal.
