# Stage 18 — Mozc telemetry excision

`tools/remove_mozc_telemetry_complete.py` physically removes the Mozc/Japanese metrics module root, Clearcut observer/helper, timing observer/enum, generated provider interfaces, visual-metric listener/event state, decoder timing call, and orphan event emitters.

The pass is guarded by source markers, the exact generated module registry, synthetic-switch discriminators, inbound-reference checks, and a four-DEX rebuild. It refuses to run when the expected metrics graph is absent or when a retained source still references a deleted event class.

Preserved functionality:

- Japanese/Mozc input engine
- conversion and candidate generation
- transliteration
- user dictionaries
- local learning and personalization

This stage changes observers and event-export paths only; it does not delete the Japanese input engine or its local model/data paths.
