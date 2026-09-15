# Meboard Stage 45 — Voice Donation Promo construction removal

Status: signed cumulative test candidate; static/build verification PASS; runtime pending; privacy-final NO.

Base: user-confirmed working Stage 44, SHA-256 `347127345444ba672e6335226984dddaf20262350b5c31cac347af18f17d14fe`.

Candidate APK: `Meboard-stage45-VOICE-DONATION-PROMO-INIT-REMOVED-TEST.apk`, SHA-256 `0eb4edc0f15917bdafdc32dafdbe3a1d9078f6a7dbf9dbd4fe30eb45f2dda3a2`.

Stage 45 removes the two live `VoiceDonationPromoManager` (`kgd`) construction/initialization blocks: the standard `VoiceInputManager` path in `kgm.f(...)` and the NGA input path in `NgaInputManager.o()`. Both stock paths already nulled their donation-manager field before conditionally constructing `kgd`; those null assignments are preserved and the subsequent donation eligibility/logging/construction blocks are physically excised.

Fresh signed-output comparison against Stage 44: exactly one APK payload changes (`classes.dex`). Main-DEX class count remains 7461 -> 7461, with zero classes added/deleted. Exactly two existing classes change: `kgm` and `NgaInputManager`. `classes2.dex`, DEX 3/4, manifest, resources, settings XMLs, assets and native libraries are byte-identical to Stage 44.

No `new-instance ... Lkgd;` or `Lkgd;-><init>(Context,rqn)` construction site remains. The `maybeInitializeVoiceDonationPromoManager` marker is absent from both modified paths.

Locked cumulative removals remain absent (`rqw`/VoiceDonationManager, `maybeAddDonationRequest`, `psa`, `psp`, `mck`, `mcj`). Moonshine helper classes are byte-identical to Stage 44 and `org.futo.voiceinput.moonshine` plus deferred `commitText()` handling remain present.

The `kgd` implementation and remaining static/lifecycle references are deliberately retained for this bounded stage. After runtime acceptance, the next pass will classify/excise those remaining donation-only references and physically delete the resulting closed promo/dialog/banner cluster.

Signature/package checks: APK v3 signature PASS with the permanent Meboard certificate `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`; v1/v2/v4 false; ZIP integrity PASS; 16-KiB native alignment PASS; Apktool 3.0.3 fresh decode PASS; `aapt2` resolves package `com.mekromn.meboard`, label `Meboard`, version code `175940518`.

Runtime gate: keyboard opens/types; short mic tap normal Meboard dictation; long mic press launches Moonshine; returned transcription inserts into original editor; no voice-donation banner/dialog appears during normal use.
