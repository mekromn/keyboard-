# Meboard account isolation / federated runner checkpoint

Privacy contract: preserve all user-facing Gboard features and local/on-device AI, while preventing Google account association, unnecessary outbound telemetry, and sharing of local model/training state.

## Account isolation completed in the current build pipeline

- Removed `android.permission.GET_ACCOUNTS`.
- Removed `AccountsCapabilitiesChangedReceiver` registration and implementation.
- Removed raw `AccountManager.get()` / `getAccounts()` device-account enumeration.
- Removed device-account email seeding from the Delight5 local Email LM while keeping the Email LM and locally learned email data.
- Removed the dedicated account-only Email LM refresh runnable.
- Removed Mozc/Japanese `__auto_imported_self_accounts` import while preserving Mozc, user dictionaries, contact dictionary handling, and local learning.
- Removed the discarded AccountManager acquisition in the Mobile Data Download dependency path while preserving downloads.
- Forced Help/Feedback request identity onto the existing anonymous path; device Google account names are no longer selected.
- Removed account-derived state writes from LatinMetricsProcessor and DailyPing.
- Physically deleted `AndroidAccountUtils` (`mpo`) and the GoogleAuthUtil/GMS `get_accounts` provider (`ksg`) after their consumers were cut.
- Removed the `AccountsStatusCheckerModule` registry root, Dagger component provider, account-change listener, capability receiver, and implementation cluster.

Current targeted scans: zero direct `AccountManager.get`, zero `getAccounts`, zero GMS `get_accounts`, zero `GET_ACCOUNTS` permission, zero `mpo`, and zero `mph` references.

## Federated execution removal completed

- DynamicTrainer module removed while preserving LocalComputationTaskManager.
- Native federated runner branch physically deleted from the mixed in-app training service. The retained local-computation branch still uses `NativeLCRunnerWrapper`.
- `NativeFLRunnerWrapper` and its callback deleted.
- Public `runFlTraining(...)` API deleted.
- Binder transaction 2 and its FL adapter deleted.

This removes the app-visible/native federated training execution path while preserving local computation / local AI execution.

## Remaining verifier work

Strict static verification still reports orphaned registration resources/assets and shared-library residue containing Clearcut/Primes/Phenotype/Brella strings. These are being audited next. A build is not final until actual active telemetry/transport implementation and unnecessary configuration payloads are physically absent and the APK rebuilds/signs successfully.
