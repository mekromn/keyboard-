# Meboard Stage 55 — selected Gboard-patches feature port

Base: Stage54n (`meboard/stage54n-fix-transparent-voice-sound-emoji-hold-20260916`).

Artifact: `Meboard-stage55-GBOARD-PATCHES-FEATURES-TEST.apk`

SHA-256: `1e72782b6125f58c3a2e391ffe56309352032b9010892f282119ab0d7ca7d928`

Package: `com.mekromn.meboard`

versionCode: `175940525`

versionName: `18.0.3.954559732-meboard55x`

## Ported feature families

1. Key Shape Selection
   - Forces only `more_pill_keys` rollout gate TRUE through Meboard's central flag-result seam.
   - Does not select rounded/pill keys by default.
2. Use Bluetooth Microphone
   - Forces only `enable_use_bluetooth_setting` TRUE, exposing the native Voice typing control.
3. Hyperspeed Typing Animation
   - Forces `enable_llm_pc` and `enable_llm_pc_flow_mode` TRUE.
   - Forces `llm_pc_supported_language_tags` to `*`.
   - Positive text-key events are mapped to the stock typing-pulse code `-10043`, preserving control keys 55/56/59/60/62/66/67.
4. Top Toolbar Item Count
   - Adds a Settings > Preferences dropdown for 3–8 items, default 6.
   - Applies to the live AccessPointsBar and the two toolbar count flags.
5. Clipboard Enhancements
   - Preserves the existing Meboard 1/3/6/12/24-hour retention dropdown.
   - Adds item limits 10/100/Unlimited.
   - Adds preview lines 5/10.
   - Adds retention countdown, creation-time label, order index, grid columns 1/2/3.
   - Adds optional first-1,000-character clipboard-card rendering.

## Payload boundary versus Stage54n

- Non-signature ZIP entry set unchanged: 9,150 entries.
- Changed payloads only: `AndroidManifest.xml`, `classes.dex`, `classes2.dex`.
- `classes3.dex`, `classes4.dex`, `resources.arsc`, built-in themes, Meboard themes, and all native libraries are preserved.
- Main DEX: 5 existing classes changed, none added/deleted.
- DEX2: 5 existing classes changed, 6 Meboard classes added, none deleted.

## Packaging gates

- Fresh Apktool 3.0.3 decode: PASS.
- ZIP integrity: PASS.
- 16-KiB zipalign: PASS.
- APK Signature Scheme v3: PASS.
- Stable signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`.

Runtime Android/IME verification is still pending device testing.