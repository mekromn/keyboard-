# Meboard Stage 31a — startup verifier repair

Status: signed test APK; static/build verification PASS; phone runtime pending; privacy-final NO.

## Stage 31 failure

Stage 31 inserted the bounded glass-background refresh near the end of `oup.onStartInput(EditorInfo, boolean)`. Stock code initially stores the `Loup` service object in local `v0`, but later executes `iget-object v0, v0, Loup;->ag:Louq;`, so `v0` becomes a `Louq` object. Stage 31 then incorrectly executed `iget-object v1, v0, Loup;->j:...` through the already-overwritten register. That is a verifier-invalid receiver type and explains the startup failure when ART verifies/loads the input-service class.

Stage 31a saves the valid `Loup` instance in low register `v14` immediately before stock code overwrites `v0`, then the Meboard glass refresh reads `Loup.j` from `v14`. The stock `Louq` path is otherwise unchanged.

## Preservation

Compared with the signed Stage-31 APK, Stage 31a changes exactly one decoded class: `oup`. The other 21,749 decoded classes are byte-identical. AMOLED Theme-radio helpers, the `SoftKeyboardView` long-press interception, `VoiceProviderChooser`, `mhe`, `mic`, `jsq`, and `jxe` are byte-identical to Stage 31.

Exactly one decompressed APK payload changes: `classes.dex`. `resources.arsc`, AndroidManifest, launcher assets, and all 16 native libraries are byte-identical. ZIP CRC, 16-KiB native alignment, and APK Signature Scheme v3 pass with the permanent Meboard certificate.

Output APK: `Meboard-stage31a-STARTUP-FIX-AMOLED-ThemeRadio-VoiceLongPress-TEST.apk`
SHA-256: `1e7cc1488d3ddd713639cdac9ef595e24e363fe3ba13d3b91847443784387172`
Package: `com.mekromn.meboard`
Version code: `175940518`
Signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`

Stage 31 is failed and is not a rollback. Stage 27 remains the last user-confirmed working rollback. Runtime-test startup first; only then test the AMOLED Theme background choice and microphone long-press provider chooser. Privacy cleanup remains incomplete.
