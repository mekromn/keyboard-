# Meboard Stage 47 — final live static donation triggers removed

Status: signed cumulative test candidate; static/package verification PASS; device runtime pending; privacy-final NO.

## Exact artifact
- APK: `Meboard-stage47-DONATION-STATIC-TRIGGERS-REMOVED-TEST.apk`
- SHA-256: `6b159afb25403537c8143bf50c52e61905c982422b2b65597b3cfdd1ff870278`
- Size: 110205872 bytes
- Package: `com.mekromn.meboard`
- Input: exact user-confirmed Stage 46 APK, SHA-256 `a7ea4a0355b813f98b6d0e043f156e51364821cb24adf80628d53a3c8f604700`
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

## Removal
Stage 45 removed both VoiceDonationPromoManager constructors. Stage 46 removed dead instance fields/lifecycle plumbing. Stage 47 removes the last two live static donation triggers from outside the donation cluster:

1. `kgm.f(Lnur;)Z` no longer invokes `kgd.f(Context)` from normal voice flow.
2. The VoiceImeExtension lifecycle branch in `gau` no longer invokes `kgd.i(Context)` and returns immediately.

There are no `new kgd(...)` constructor calls left. The removed privacy preference no longer instantiates the old donation preference-listener selector. The dedicated static donation dialog/banner implementation remains packaged for one final runtime gate; after Stage 47 it has no constructor path or live external static entry point.

## Package boundary
Compared with Stage 46, exactly one decompressed APK payload changes: `classes.dex`.

Byte-identical to Stage 46: `classes2.dex`, `classes3.dex`, `classes4.dex`, `AndroidManifest.xml`, `resources.arsc`, cleaned privacy XMLs, assets, and all native libraries.

Fresh decode shows exactly two changed main-DEX smali classes: `gau` and `kgm`; no class added or deleted.

## Regression gates
PASS: prior VoiceDonationManager removal; Stage-44 user metrics removal; external kgd.f/kgd.i triggers absent; `org.futo.voiceinput.moonshine` present; Moonshine relay/chooser/deferred-result helper smali byte-identical to Stage 46; APK v3 signature PASS; 16-KiB alignment PASS.

## Runtime gate
Verify normal typing, short-tap Meboard dictation, long-press Moonshine, returned Moonshine text, no voice-input crash/hang, and no voice-donation UI. After a pass, Stage 48 can physically delete the now-unreachable static donation dialog/banner cluster and donation-only synthetic selector cases.
