# Meboard keyboard split-resource ID repair — 2026-09-05

## Device failure

After the `LatinApp.e()` register repair, Meboard's application and input-method
service could start, but the keyboard never became visible. Android repeatedly
bound `com.android.inputmethod.latin.LatinIME`, requested IME visibility, and
then restarted the process after this fatal error:

```text
java.lang.AssertionError:
Exception from receiver.onKeyboardDefReady():
Failed to fetch keyboard for prime when activating

Caused by: java.lang.IllegalStateException:
Failed to get identifier from name: 0
```

The failing path ended in `KeyboardSource$Xml.a()` after resource resolution
through `rpu`, `rqi`, `pmz`, `ppo`, and `ppv`.

## Root cause

The original Gboard delivery is split. The xxhdpi density split contributes both
resource files and `public.xml` declarations that preserve their assigned
`0x7f...` resource IDs.

The monolithic Meboard fusion copied the split-backed files but did not merge all
of the split's public resource declarations. AAPT therefore assigned different
IDs while decoded base keyboard XML still contained unresolved `@null` values.
At runtime a required keyboard attribute was converted to the literal resource
name `0`; `Resources.getIdentifier("0", ...)` failed and the IME process died.

This was broader than one popup icon. Fixing only the first observed reference
would have exposed the next zero-valued reference immediately afterward.

## Complete repair

The repair derives the resource identity from the untouched supplied bundle and
applies it before the final monolithic resource build:

- **114** resource IDs contributed by the density split are merged with their
  original type, name, and numeric ID;
- **194** lost resource references are restored;
- the references span **48 XML files**;
- split `values` resources are merged as well as file-backed drawables, including
  the split-contributed integer resource;
- every affected source location is assertion-checked rather than replaced by a
  broad text substitution.

## Verification

The corrected compiled APK must satisfy all of the following:

1. all 114 split declarations exist with their original numeric IDs;
2. all 194 repaired attributes compile as typed resource references, never
   integer zero or the string/name `0`;
3. every affected XML source is free of the corresponding `@null` placeholder;
4. `resources.arsc` contains the merged declarations;
5. all four DEX files are byte-identical to the previous build that reached
   `LatinIME` startup;
6. all 16 native libraries are byte-identical to that build;
7. the earlier `LatinApp` Context-register and `eqt` registry gates still pass;
8. the APK passes ZIP integrity, APK Signature Scheme v3 verification, and 16 KiB
   native-library alignment;
9. the package remains `com.mekromn.meboard` with the established Meboard signer.

The resource fix does not restore any account, telemetry, reporting, federated,
or certificate-whitelist code and does not remove any user-facing feature.

## Runtime gate

Static verification is not a substitute for device behavior. The exact promoted
candidate must still pass:

1. install/update without uninstalling;
2. `LatinIME` bind;
3. keyboard surface render;
4. continuous typing and suggestions;
5. switch to another IME;
6. switch back to Meboard;
7. retained-feature regression testing.

No deeper privacy-removal stage is promoted until this runtime gate is recorded.

## Redundant checkpoint

The corresponding local/Library checkpoint is:

```text
/Meboard/Checkpoints/20260905T133500Z
```

It contains the signed APK, checksum sidecar, machine-readable promotion report,
human-readable verification, a public recovery archive, a private recovery
archive, and a one-file resume document. The private archive contains proprietary
application material and must never be published.
