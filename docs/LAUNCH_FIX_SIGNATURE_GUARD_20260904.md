# Meboard launch repair: upstream APK certificate whitelist

Target: Meboard based on Gboard 18.0.3.954559732, package `com.mekromn.meboard`.

## Device evidence

On the Pixel 9 Pro XL running Android 16, APKbox captured the process fatal after the independently signed Meboard update:

```text
FATAL EXCEPTION: Back-P10-1
Process: com.mekromn.meboard
java.lang.IllegalStateException: APK is signed by unrecognized certificates:
23E8720F08B5975B28FDDA85586AB1E7E8422C64082E6A0E221F657C0B7A4E15
    at mm.run(PG:526)
```

That digest is Meboard's legitimate stable signing certificate. The crash was not Android rejecting the APK. Android Package Manager had already installed it successfully. The failure came from application code inherited from Gboard.

## Root cause

`LatinApp` scheduled synthetic `Runnable` class `mm` with discriminator `8` during application startup.

That branch:

1. obtained Meboard's package name;
2. calculated the installed signing-certificate digest through `SignatureUtils` (`rpv`);
3. compared it with four hard-coded Google certificate digests;
4. constructed and threw `IllegalStateException` when the signer was not Google-recognized.

Any legitimate independently signed fork therefore crashed by design.

## Physical repair

`tools/remove_signature_whitelist_guard.py` physically removes:

- the sole `LatinApp` scheduling callsite for discriminator `8`;
- the discriminator-8 executable branch from `mm.run()`;
- the exception message, constructor, and throw path;
- the `rpv.a(Context, String)` whitelist comparator;
- the four embedded recognized-certificate byte arrays.

The impossible packed-switch entry is retargeted to the existing common return label after its producer has been removed. No hostname block, configuration flag, catch-and-ignore shim, fake certificate, or no-op verifier class is used.

Android's normal package-signature and update-signature enforcement is unchanged. Future Meboard updates remain required to carry the stable Meboard certificate.

## Reproducibility

`tools/replay_meboard_launchfix.py` reconstructs the complete stage-16 privacy tree from the untouched source bundle, applies this physical certificate-whitelist removal, verifies the generated module registry's register state, rebuilds all four DEX files, and validates ZIP integrity.

The locally replayed unsigned checkpoint produced on 2026-09-04 had SHA-256:

```text
41895025a92a063d7b1cb6caf76b1464955805f9265d4c1d40e7c25a1adcbda8
```

The incrementally rebuilt and stable-key-signed device candidate had SHA-256:

```text
5a47c72c6a613c50b9259d3a25d2d38d84bd26ad1f3433c6afc902ff72caa432
```

It retained package `com.mekromn.meboard`, four DEX files, APK Signature Scheme v3, the stable Meboard signer, and 16 KiB native-library ZIP alignment.
