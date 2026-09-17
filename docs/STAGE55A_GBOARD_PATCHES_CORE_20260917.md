# Meboard Stage 55a

Base: Stage 54n.

Ports the four non-clipboard features requested from jasonwu1994/Gboard-patches for the exact Gboard 18.0.3.954559732 target:

- Key Shape Selection: forces only `more_pill_keys=true`; does not choose a rounded shape automatically.
- Use Bluetooth Microphone: forces only `enable_use_bluetooth_setting=true` so the stock Voice typing control is available.
- Hyperspeed Typing Animation: adds a Meboard Preferences switch (default off), forces the upstream flow-mode rollout flags only while enabled, and bridges text keycodes through the stock FlowModeDetector pulse code while preserving control keys.
- Top Toolbar Item Count: adds a Meboard enable switch plus a 3–8 selector (override default off; count default 6), overriding only `config_max_access_points` and `config_default_access_points_num_on_bar` when enabled.

Clipboard Enhancements are intentionally separated into Stage 55b because they require the independent loader/prune/adapter/grid hook cluster.

Signed test APK SHA-256: `17869fdc8576ef59d5b66cbc66444d9f45bc2e1809e26b152dd85735bd20e952`.

Static preservation versus Stage54n: only `classes.dex` and `classes2.dex` changed. DEX 3/4, manifest, resources, themes, assets, and native libraries are unchanged. Permanent Meboard v3 signer preserved.