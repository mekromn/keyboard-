# Meboard Stage 31b — second startup verifier repair

Status: signed test APK; static/build checks pass; phone runtime pending; privacy-final NO.

## Why Stage 31a still crashed

The first repair saved `Loup` into local `v14` only near the normal tail of `oup.onStartInput(EditorInfo, boolean)`. The stock method has an existing early `goto :goto_4` used by the destroyed-service path. That branch skips the late assignment but lands directly on the added Meboard glass refresh, which reads `v14` as `Loup`. Definite-register analysis of the exact signed Stage-31a APK reproduces the fault: `v14` is uninitialized at that `iget-object` on the early predecessor.

Stage 31b initializes `v14` from the already-valid `p0`/`v0` `Loup` receiver at method entry. Stock code is still free to reuse `v14`; the existing late Stage-31a `move-object v14, v0` remains and re-pins the receiver for the normal predecessor. Thus both predecessors of the shared `:goto_4` join with `v14` defined as `Loup`.

## Artifact

- APK: `Meboard-stage31b-STARTUP-VERIFIER-FIX2-AMOLED-ThemeRadio-VoiceLongPress-TEST.apk`
- SHA-256: `7646b98b9f59d2b94c7fd20e9c6903f93dae5a6b27ef6221122e235e534f5232`
- Size: 110111660 bytes
- Package: `com.mekromn.meboard`
- VersionCode: `175940518`
- Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`
- APK Signature Scheme v3: verified

## Preservation and checks

Versus signed Stage 31a, exactly one decoded class changes: `smali/oup.smali`; the other 21749 decoded classes are byte-identical. Exactly one decompressed APK payload changes: `classes.dex`; the other 9147 non-signature payload entries are byte-identical, including resources.arsc, AndroidManifest.xml, launcher icon resources and all 16 native libraries.

The final signed Stage-31b APK was freshly decoded. Its 21750 smali class files exactly match the patched source tree. A control-flow definite-register checker covering the modified Stage-31 feature classes reports zero uninitialized local-register reads. Running the same checker against exact Stage 31a reproduces one error in `oup.onStartInput`: the Meboard glass `iget-object` reads `v14` before definition on the early path.

ZIP CRC and 16-KiB native-library alignment pass. `aapt2 dump badging` resolves application label `Meboard`, launcher activity `com.google.android.libraries.inputmethod.launcher.LauncherActivity`, and `res/mipmap-anydpi-v21/ic_app.xml` for the launcher icon.

## Runtime gate

Stage 31 and Stage 31a remain failed and must not be promoted. Stage 27 remains the last user-confirmed working rollback. Stage 31b must first pass launch-on-phone before evaluating the AMOLED theme-radio behavior or mic long-press provider chooser.
