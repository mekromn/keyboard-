# Meboard Stage 48 — physical voice-donation cluster removal + Test Meboard

Status: **signed cumulative test candidate; static/package verification PASS; phone runtime pending; privacy-final NO**.

## Exact artifact

- APK: `Meboard-stage48-DONATION-CLUSTER-REMOVED-TEST-MEBOARD.apk`
- SHA-256: `026b7a1961d515e37a38ae609ac4dc2be00c46d44cea0a4fa9179fe6e0c5497f`
- Size: `110205872` bytes
- Package: `com.mekromn.meboard`
- Version code: `175940518`
- Version name: `18.0.3.954559732-release-arm64-v8a`
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`
- Exact input: user-confirmed-working Stage 47, SHA-256 `6b159afb25403537c8143bf50c52e61905c982422b2b65597b3cfdd1ff870278`.

## Physical donation-cluster deletion

Stages 45-47 removed both `VoiceDonationPromoManager` constructors, stale instance/lifecycle plumbing, and the final live static triggers. Stage 48 uses that proven no-entry-point state to physically delete the dedicated promo/dialog/banner implementation classes:

- `kgd` — `VoiceDonationPromoManager`
- `kgb` — manager callback/listener
- `kga` — donation banner animation helper
- `kfu` — `VoiceDonationConfirmationBanner`
- `kfy` — `VoiceDonationIntroDialog`
- `kfw`, `kfx`, `kfv` — dedicated intro-dialog handlers/callbacks

No replacement/no-op versions of those classes are added.

Because several obfuscated synthetic callback classes are shared with unrelated keyboard features, they are **not** deleted. Only their donation-only selector branches are replaced by no-op returns. The affected shared classes are `jsb`, `kft`, `jte`, `ewj`, `hmj`, `fya`, `igr`, `kfz`, `haa`, `ewn`, `kcs`, `kgj`, `hel`, plus the typed donation-only constructors in `jim` and `igr`.

Fresh decode of the signed APK confirms none of the deleted class descriptors (`Lkgd;`, `Lkgb;`, `Lkga;`, `Lkfu;`, `Lkfy;`, `Lkfw;`, `Lkfx;`, `Lkfv;`) survive anywhere in packaged smali.

## Test Meboard settings option

A new **Test Meboard** row is added programmatically to the root settings screen. No resource XML or resource-table rebuild is involved.

Behavior:

1. Open Meboard settings.
2. Tap **Test Meboard**.
3. A focused multiline text box opens in an in-app dialog.
4. The activity requests the active IME immediately, providing a convenient surface for normal typing, short-tap voice input, and long-press Moonshine testing.
5. Closing the dialog changes no keyboard preference or provider default.

The row is keyed `meboard_test` and insertion is idempotent, so fragment refreshes cannot duplicate it.

## Package boundary

Stage 47 -> Stage 48 changes exactly **one non-signature APK payload**:

- `classes2.dex`

Byte-identical to Stage 47:

- `classes.dex` — includes the confirmed-working Moonshine direct-launch/deferred-result path
- `classes3.dex`
- `classes4.dex`
- `AndroidManifest.xml`
- `resources.arsc`
- `res/xml/setting_privacy.xml`
- managed-configuration XML
- assets
- all native libraries

The non-signature payload entry set is unchanged at **9143 entries**.

## DEX source delta

Stage 47 classes2 decoded classes: `9510`.
Stage 48 classes2 decoded classes: `9504`.

Net: `-6` classes = 8 dedicated donation classes deleted + 2 Test Meboard helper classes added.

Added:

- `com/mekromn/meboard/MeboardTestPreference`
- `com/mekromn/meboard/MeboardTestPreference$ClickListener`

Changed surviving files: 15, consisting of the root preference header plus the shared synthetic donation-selector hosts listed above.

## Locked regression gates

Fresh decode of the signed Stage-48 APK confirms:

- `VoiceDonationManager` / `Lrqw;`: absent
- `maybeAddDonationRequest`: absent
- removed user-metrics/collection-basis classes `psa`, `psp`, `mck`, `mcj`: absent
- dedicated Stage-48 donation class descriptors: absent
- Moonshine package `org.futo.voiceinput.moonshine`: present
- Test Meboard title/hook: present
- cleaned privacy/managed XML payloads: byte-identical to Stage 47

Some obsolete donation **preference/counter strings and generic helper methods** still remain in shared classes such as `kkl`/`icx`; Stage 48 does not falsely claim those are removed. They are smaller follow-up cleanup targets now that the functional promo/dialog implementation is physically gone.

## Signing / alignment

- APK Signature Scheme v3: PASS
- v1/v2/v4: disabled/not verified
- stable Meboard certificate: exact match
- ZIP/native 16-KiB alignment: PASS
- package/version identity: preserved
- deterministic public patch replay: PASS; independently re-applied Stage-48 patch to fresh Stage-47 decode and reassembled `classes2.dex` byte-for-byte identical (`f35c4a0256cd93fd6ed492fc2769bc8b218a186463fbf1f7f75285ab1c885eed`)

## Runtime gate

Install directly over Stage 47 without clearing data and verify:

1. Keyboard opens/types normally.
2. Short microphone tap runs normal Meboard dictation.
3. Long microphone press launches Moonshine directly.
4. Moonshine result returns into the original text field.
5. Meboard settings contains **Test Meboard**; tapping it opens the test text box and keyboard.
6. No donation banner/dialog appears and voice entry/exit remains stable.

After this passes, Stage 48 becomes the new cumulative base. Remaining work includes obsolete donation preference/counter residue, further Primes/diagnostic/Phenotype/network cleanup, and the mixed native reporting audit.
