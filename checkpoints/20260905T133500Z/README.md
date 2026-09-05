# Meboard checkpoint 20260905T133500Z

This checkpoint records the complete keyboard-definition split-resource repair.

## Current verified state

- The previous `LatinApp.e()` Context-register VerifyError remains fixed.
- Device logcat proved that `LatinIME` then failed while loading keyboard XML
  because a required resource was resolved from the literal name `0`.
- Root cause: density-split files had been fused without preserving the split's
  `public.xml` numeric IDs.
- **114** split resource declarations were merged.
- **194** lost references were restored across **48 XML files**.
- The compiled-resource verifier confirmed that repaired attributes are typed
  resource references rather than null/integer-zero values.
- All four DEX files are byte-identical to the previous build that reached IME
  startup.
- All 16 native libraries are byte-identical to that build.
- Only the resource table and affected resource XML payload changed.
- APK ZIP, stable-signature, and 16 KiB alignment gates passed.
- Runtime bind/render/type/switch validation of this exact candidate is pending.
- Privacy-final status remains **no**.

## Artifact location

Persistent Library folder:

```text
/Meboard/Checkpoints/20260905T133500Z
```

The folder contains:

- `Meboard-stage16-split-resource-id-fix-replay-signed.apk`
- its SHA-256 sidecar;
- source and compiled verification reports;
- `Meboard-RESUME-NOW-20260905T133500Z.md`;
- public and private recovery archives;
- independent archive checksum files.

The private archive contains proprietary Gboard/Meboard material and must never
be published.

## Next gate

Install the exact signed candidate over the existing same-signer Meboard build,
verify the installed base APK SHA-256, select Meboard in a normal text field, and
capture fresh logcat. Acceptance is:

1. `LatinIME` binds;
2. keyboard surface renders;
3. continuous typing remains stable;
4. switch to another keyboard;
5. switch back to Meboard successfully.

No deeper privacy-removal stage is promoted until that runtime result is recorded.

## Invariant

No user-facing keyboard feature is an approved removal target. This repair is
resource-only and does not modify DEX, native code, account isolation, telemetry
removal, or local AI/personalization behavior.
