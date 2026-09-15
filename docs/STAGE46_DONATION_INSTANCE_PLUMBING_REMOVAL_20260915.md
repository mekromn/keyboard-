# Meboard Stage 46 — donation promo instance/lifecycle plumbing removal

Status: **signed cumulative test candidate; static/build verification PASS; phone runtime pending; privacy-final NO**.

## Exact artifact

- APK: `Meboard-stage46-DONATION-INSTANCE-PLUMBING-REMOVED-TEST.apk`
- SHA-256: `a7ea4a0355b813f98b6d0e043f156e51364821cb24adf80628d53a3c8f604700`
- Size: **110,205,872 bytes**
- Package: `com.mekromn.meboard`
- Version code: `175940518`
- Version name: `18.0.3.954559732-release-arm64-v8a`
- Base: user-confirmed working Stage 45
- Stage-45 SHA-256: `0eb4edc0f15917bdafdc32dafdbe3a1d9078f6a7dbf9dbd4fe30eb45f2dda3a2`
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

## Scope

Stage 45 removed both live `VoiceDonationPromoManager` (`kgd`) construction sites. Stage 46 removes the now-impossible **instance/lifecycle plumbing** that remained around those objects while deliberately leaving the separate static donation consent/reset/dialog path for the next pass.

Physical/member removals in Stage 46:

- delete `kgw.u:Lkgd;` field;
- delete `NgaInputManager.l:Lkgd;` field;
- delete donation-only `kgm.l()V` helper and both call sites;
- delete donation-only `kgw.j()V` helper and its remaining call site;
- remove the stale `kgw.u = null` write in the standard voice startup path;
- remove `kgw.r(...)` donation `h()` lifecycle tail;
- remove NGA `s()/c()/o()` donation field/lifecycle blocks while preserving TalkBack, timer, oration, SmartEdit and other non-donation behavior;
- remove the `kgv.k(...)` donation lifecycle callback;
- remove the `ihv.run()` NGA donation lifecycle callback.

This stage does **not** remove the still-independent static donation methods such as `kgd.f/g/i/l` or their consent/dialog handlers. Those are intentionally deferred until their remaining callers are excised.

## Exact signed-output source delta

Fresh Apktool source decode of the actual signed Stage-45 and Stage-46 APKs:

- total decoded class files: **21,746 -> 21,746**
- classes added: **0**
- classes deleted: **0**
- exactly five changed classes:
  1. `kgm`
  2. `kgw`
  3. `com.google.android.apps.inputmethod.libs.nga.impl.input.NgaInputManager`
  4. `kgv`
  5. `ihv`

The following stale references are absent from the final signed decode:

- `Lkgw;->u:Lkgd;`
- `NgaInputManager;->l:Lkgd;`
- `Lkgm;->l()V`
- `Lkgw;->j()V`

Remaining `Lkgd;` inventory after this stage: **19 files / 99 descriptor occurrences**, down from Stage 45's 23 files. These are confined to the still-separate static donation implementation/handlers and no longer include standard/NGA manager instance fields.

## Package boundary

Stage 45 -> Stage 46 preserves the exact same **9,143 non-signature payload entry names**. Exactly two decompressed APK payloads change:

1. `classes.dex`
2. `classes2.dex`

Byte-identical to Stage 45:

- `classes3.dex`
- `classes4.dex`
- `AndroidManifest.xml`
- `resources.arsc`
- `res/xml/setting_privacy.xml`
- `res/xml/APKTOOL_RENAMED_0x7f170002.xml`
- all assets
- all native libraries
- all other resources/payloads

DEX format is preserved:

- `classes.dex`: `dex\n040`
- `classes2.dex`: `dex\n039`
- `classes3.dex`: `dex\n040`
- `classes4.dex`: `dex\n039`

The two affected DEX files were assembled directly from the decoded Stage-45 tree using the pinned Apktool/Smali implementation, then injected into the untouched Stage-45 APK container. No resource-table rebuild was performed.

## Cumulative removal regression gates

The signed Stage-46 decode confirms all previously locked removals remain absent:

- `rqw` / `VoiceDonationManager`
- `maybeAddDonationRequest`
- `PrivacySettingsFragment.aD(boolean)`
- `psa`
- `psp`
- `mck`
- `mcj`

The cleaned privacy and managed-configuration XML payloads are byte-identical to user-confirmed Stage 45, so the removed settings remain carried forward unchanged.

## Moonshine regression gate

The working external voice-input feature remains present:

- direct target `org.futo.voiceinput.moonshine`: present;
- `VoiceResultCommitRunnable`: present;
- deferred `InputConnection.commitText()` return path: present;
- manifest/resources related to Stage-45 behavior: byte-identical.

No Moonshine helper class is among the five changed classes.

## Signature / packaging verification

- APK Signature Scheme v3: **PASS**
- v1: false
- v2: false
- v4: false
- permanent Meboard certificate: **exact match**
- RSA key size: 4096 bits
- ZIP integrity/alignment check: **PASS**
- 16-KiB native-library alignment: **PASS**
- `aapt2 dump badging`: package/version resolve correctly
- fresh signed-output Apktool source decode: **PASS**

## Next safe removal

After runtime confirmation, the donation cleanup can move to the remaining **static consent/reset/dialog path**. The remaining `kgd` callers are now much easier to classify because standard and NGA voice managers no longer own donation-manager instances.

The next pass should remove static donation entry points from shared synthetic handlers first, then delete the closed `kgd` / banner / dialog helper cluster only after the graph reaches zero surviving ingress.

## Runtime acceptance gate

Install directly over Stage 45 without clearing data and verify:

1. keyboard opens and types normally;
2. short microphone tap still runs normal Meboard dictation;
3. long microphone press launches Moonshine directly;
4. Moonshine result returns into the original field;
5. NGA/voice lifecycle transitions do not crash or hang;
6. no voice-donation banner/dialog appears.

Only after this passes should Stage 46 replace Stage 45 as the locked cumulative base.
