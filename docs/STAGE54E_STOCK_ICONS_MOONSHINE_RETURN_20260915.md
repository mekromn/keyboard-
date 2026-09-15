# Meboard Stage 54e — exact stock keyboard resources + immediate Moonshine return

Status: **signed test APK; static/build verification PASS; user runtime test pending**.

## Base

Stage 54e is cumulative from the user-confirmed-working **Stage 54d**. Stage54d's true native incognito/learning behavior, native incognito header icon, Stage54c Space long-press Select All/Copy, Clipboard timeout dropdown, Test Meboard, Moonshine provider targeting, and all locked privacy/removal work are preserved unless explicitly described below.

## Correction: second blank key was not proven to be Emoji

The Stage54c/54d visual patch assumed the second blank key was the Emoji/Smiley position. The stock ASPK supplied by the user proves that assumption was not justified.

Stock does name view positions `key_pos_switch_to_emoticon` (`0x7f0b0608`) and `key_pos_switch_to_smiley` (`0x7f0b060a`), but the actual resource-table damage found in Meboard is a different problem: the main keyboard theme style `0x7f15043d` lost **ten split-backed stock drawable references** and rebuilt them as `@null`.

The missing stock references are:

- `0x7f040195 -> 0x7f0805a5`
- `0x7f0401a1 -> 0x7f0805eb`
- `0x7f0401a3 -> 0x7f0805f4`
- `0x7f0401a4 -> 0x7f0805f6`
- `0x7f0401b0 -> 0x7f0805fb`
- `0x7f0401b1 -> 0x7f0805fc`
- `0x7f0401b2 -> 0x7f0805fd`
- `0x7f0401b5 -> 0x7f080600`
- `0x7f0401bc -> 0x7f08056e`
- `0x7f0401bd -> 0x7f08056f`

The stock mapping registry independently identifies `0x7f0805fb` / `0x7f0805fc` / `0x7f0805fd` as Shift locked / Shift off / Shift on. Their packaged WebP bytes in Meboard are byte-identical to the user's stock xxhdpi split; only the theme references were missing.

The stock Emoji resource `0x7f0805a2` was already intact in Meboard and resolves to `0x7f0804c4`; it was **not** one of the lost `@null` mappings.

### Stage54e icon fix

Stage54e therefore removes the entire Stage54d `SoftKeyView` guessed-icon override and restores the **ten exact stock theme references** instead.

This is a surgical binary `resources.arsc` edit:

- table size is unchanged: `19,611,312` bytes;
- only **39 bytes** differ from Stage54d;
- fresh `aapt2 dump resources` shows exactly the ten intended semantic changes and nothing else;
- no resource paths, qualifiers, IDs, XML payloads, or drawable bytes are rebuilt.

`SoftKeyView` is restored byte-for-byte to the confirmed Stage53/54b implementation (`f7f6e54c...61795`).

## Moonshine -> keyboard immediate return

Launching Moonshine through `android.speech.action.RECOGNIZE_SPEECH` hands foreground focus to an external Activity, so Android may hide the IME while Moonshine owns that window. Stage54e does not claim it can reliably keep an IME window visible underneath another app's foreground Activity.

Instead Stage54e makes the return deterministic and immediate:

1. `VoiceProviderRelayActivity` receives Moonshine's result (or cancellation) and calls `finish()`.
2. **25 ms** later `VoiceImeRestoreRunnable` calls `VoiceProviderChooser.restoreIme()`.
3. `restoreIme()` uses the already-cached live Meboard `InputMethodService` and calls Android `InputMethodService.requestShowSelf(0)`.
4. Returned transcription commit now begins after **75 ms** instead of 300 ms.
5. Every commit/retry attempt calls `restoreIme()` first.
6. Successful commit calls `restoreIme()` once more before pending state is cleared.
7. The existing bounded retry loop remains as the safety net while the original editor regains its live `InputConnection`.

The intended visible sequence is now: Moonshine closes -> Meboard is requested visible immediately -> transcription is inserted into the original editor. No tap on the field should be needed.

## Exact Stage54d -> Stage54e APK boundary

Non-signature payload names: **9143 -> 9143, identical set**.

Changed payloads only:

- `classes.dex`
- `resources.arsc`

Byte-identical to Stage54d:

- `classes2.dex`, `classes3.dex`, `classes4.dex`
- `AndroidManifest.xml`
- every packaged resource file/drawable/XML other than the resource table
- settings/privacy XMLs
- assets
- all native libraries

Fresh signed decode class delta:

- added: `com.mekromn.meboard.VoiceImeRestoreRunnable`
- changed: `VoiceProviderChooser`, `VoiceProviderRelayActivity`, `SoftKeyView`
- deleted: none
- `SoftKeyView` change is solely removal of the Stage54d guessed-icon override; it exactly equals the Stage53/54b stock-rendering implementation.
- Stage54d native incognito listener `mlq` is byte-identical and remains active.

## Signed artifact

- APK: `Meboard-stage54e-STOCK-ICON-RESTORE-MOONSHINE-RETURN-TEST.apk`
- SHA-256: `16e48e08a3773b1448942f7a2e2ba639c70bc7598dc2b2a777ec342ad80da8b8`
- ZIP integrity: PASS
- fresh Apktool 3.0.3 signed decode: PASS
- DEX: 039 / API 28 assembly
- APK Signature Scheme v3: PASS
- permanent Meboard signer certificate preserved
- 16-KiB alignment: PASS

## Runtime gate

No connected Android/ADB runtime is available in this environment, so runtime PASS is not claimed. On-device test order:

1. Test Meboard -> keyboard renders.
2. Confirm the previously blank Shift/Caps key now uses the exact stock icon and changes normally across off/on/locked states.
3. Confirm the second previously blank button now renders its stock icon; do **not** assume it is Emoji—report its resulting icon/action if it remains wrong.
4. Long-press mic -> Moonshine -> finish recognition. Meboard should reappear immediately and the returned text should be inserted without another tap.
5. Recheck true-incognito 4-square toggle/native hat-glasses status icon.
6. Recheck Space Select All/Copy and Clipboard history timeout dropdown.
