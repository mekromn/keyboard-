# Meboard continuation — stage 17+

The verified working-tree checkpoint at the start of this continuation was the four-DEX stage-17 APK after physical removal of the Mozc Clearcut processor/helper, Mozc timing processor/enum, module provider, generated Dagger interfaces, visual-metrics listener branch, and decoder timing call.

Preserved functionality includes Japanese/Mozc conversion, candidate generation, transliteration, user dictionaries, local learning, Latin typing, local language models, dictation, handwriting, and user-triggered feature transports.

This continuation adds two repository-level safety tools:

- `tools/verify_meboard_privacy_fast.py`: an indexed decoded-tree acceptance gate for AccountManager/GMS account discovery, GET_ACCOUNTS, account-status receivers, federated runners/services, active Clearcut/Primes transport, remote Phenotype registration, Cronet telemetry opt-in, and Keyhound collection.
- `tools/audit_native_privacy.py`: an ELF symbol/string/section/relocation inventory used before any edit to `libintegrated_shared_object.so`.

The current engineering rule remains unchanged: a marker is not deleted merely because its name looks suspicious. Executable/registered privacy paths are physically removed; shared local inference/decoder code is retained; native functions are eligible only after range, relocation, and incoming-call analysis proves they are detached from retained features.
