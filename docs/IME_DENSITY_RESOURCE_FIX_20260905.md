# Meboard IME density-resource repair — 2026-09-05

## Device symptom and fatal stack

The previous candidate started `LatinIME`, Android requested the IME window, and the process then died repeatedly. The fatal stack was:

```text
java.lang.AssertionError: Exception from receiver.onKeyboardDefReady():
Failed to fetch keyboard for prime when activating

Caused by: java.lang.IllegalStateException:
Failed to get identifier from name: 0
```

The failure occurred while `KeyboardSource$Xml` loaded the keyboard definition through `pmz`, `rqi`, and `rpu`.

## Root cause

The monolithic Meboard build copied the xxhdpi split's files but intentionally skipped its `values/public.xml` table. AAPT therefore assigned unrelated IDs to the copied split resources, while Apktool's base-only decode had converted references to those split-only IDs into `@null`.

Exact compiled-XML comparison found:

- 114 density-only public resource IDs missing from the base table;
- 194 original nonzero references compiled as zero/null;
- 48 affected XML resources;
- 42 affected `popup_icon` attributes, plus `value`, `drawable`, `key_image`, `src`, `icon`, and `slideup_icon` references.

The keyboard loader converted one null reference into the literal resource name `0`, causing the observed fatal error.

## Repair

`restore_density_split_resource_ids.py`:

1. merges all 114 split-only public entries at their original IDs;
2. verifies every file-backed or `values-xxhdpi` resource source exists;
3. restores the exact 194 `(file, line, attribute, target ID)` references lost by base-only decoding;
4. rejects ID collisions, missing sources, line drift, and unexpected counts.

The exact 194-entry map is compressed in the source file only for readability; it decodes to explicit repair tuples and is not a heuristic scan.

`verify_density_split_resource_ids.py` validates the rebuilt binary rather than trusting source XML. It requires:

- all 114 resources to exist uniquely at their original IDs;
- all 194 compiled attributes to be `TYPE_REFERENCE` values pointing to the exact original target IDs.

Expected success text:

```text
density split fusion verified: 114 fixed resource IDs, 194 restored XML references across 48 XML resources
```

## Regression containment

The replay-signed fixed APK has SHA-256:

```text
913b5e69997541ad6015d80661677f510826cfd63980b85a9178a95b71780342
```

Compared with the previous Context-fixed candidate:

- all four DEX payloads are byte-identical;
- all 16 native libraries are byte-identical;
- no class, method, privacy removal, local-AI path, or user-facing feature was changed by this repair;
- only `resources.arsc` and the affected resource XML payloads changed;
- a keyed original-vs-fixed comparison reports zero original nonzero references remaining zero.

The APK passes ZIP integrity, 16 KiB alignment, APK Signature Scheme v3, the stable Meboard signer, `eqt` register-state verification, module-registry ordering/constructor verification, `LatinApp.e()` Context-register verification, and the new compiled density-resource verifier.

## Status

Static/build verification passed. Runtime success is not claimed until this exact APK is installed and passes `LatinIME` bind, render, continuous typing, switch-away, and switch-back testing. The wider privacy-removal project also remains unfinished until residual native/outbound reporting gates are completed.
