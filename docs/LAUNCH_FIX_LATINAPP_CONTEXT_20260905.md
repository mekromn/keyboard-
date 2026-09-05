# Meboard launch repair: retained `LatinApp.e()` Context producer

Target: Meboard based on Gboard 18.0.3.954559732, package `com.mekromn.meboard`.

## Device evidence

The exact installed APK was verified on the Pixel 9 Pro XL as SHA-256:

```text
dd8044ae0c365d6e7fbc6a87295cedd6c06bcf87027cdda287b9b9ef8021ffb5
```

Android 16 rejected `LatinApp` before `Application.onCreate()`:

```text
java.lang.VerifyError: Verifier rejected class
com.google.android.apps.inputmethod.latin.LatinApp:
LatinApp.e(): [0x627] register v7 has type Reference java.lang.Object
but expected Reference: android.content.Context
```

## Root cause

The upstream certificate-whitelist scheduler first called
`getApplicationContext()` and stored that `Context` in register `v7`. It then
constructed the signature-check `mm` Runnable and scheduled it.

The first physical-removal pass deleted the complete scheduling block. That
correctly removed the certificate check, but it also deleted the shared
`getApplicationContext()` producer. A later retained startup path still passes
`v7` to `qhy.I(Context)`. At that point `v7` held an unrelated `Object`, so ART
rejected the method.

## Repair

`remove_signature_whitelist_guard.py` now preserves only:

```smali
invoke-virtual {v0}, LatinApp;->getApplicationContext()Landroid/content/Context;
move-result-object v7
```

It still physically deletes:

- the executor load used by the certificate-check producer;
- the `mm` Runnable construction;
- discriminator `8`;
- the `Executor.execute()` call for that Runnable;
- the discriminator-8 body from `mm.run()`;
- the `rpv.a(Context, String)` certificate comparator;
- the exception construction/throw path;
- the four embedded Google certificate digests.

No certificate guard, telemetry path, account path, or user-facing feature is
restored. Android Package Manager's normal signer/update enforcement remains.

## Regression gate

`verify_latinapp_context_register.py` requires:

1. exactly one retained `v7` application-Context producer in `LatinApp.e()`;
2. the retained `qhy.I(v7)` Context consumer to be dominated by that producer;
3. no write to `v7` between producer and consumer;
4. absence of the signature-check discriminator/Runnable construction.

The gate deliberately permits unrelated `Executor.execute()` calls used by
retained startup behavior.

## Candidate

Clean replay, four-DEX build, 16 KiB alignment, and APK Signature Scheme v3
verification produced:

```text
Meboard-stage16-LatinApp-context-fix-replay-signed.apk
SHA-256: 30e0d61df7f88a06d835f61e5f16ed80b204b366e5d968606df777d3f8acd069
Signer certificate SHA-256: 23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15
```

Runtime launch/IME validation remains a separate gate and must be recorded from
the exact installed candidate before further privacy removal is promoted.
