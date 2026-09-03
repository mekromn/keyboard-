# Meboard Account / AccountManager Audit

Target source: Gboard 18.0.3.954559732 arm64 bundle, audited from decoded smali before account-isolation removal.

Privacy contract: Meboard should behave as logged out whenever possible, never expose/broadcast the device Google account, preserve user-facing keyboard features and local/on-device AI, and allow only deliberately user-triggered anonymous networking where possible.

## 1. Direct Android AccountManager users

### `dov.n(Context)` — raw device account-name enumeration

Direct calls:
- `AccountManager.get(context)`
- `AccountManager.getAccounts()`

Behavior:
- Iterates every returned Android `Account`.
- Reads `Account.name`.
- Filters names through `ggy.B(...)` (email-like validation).
- Returns the selected account names as plain strings.

Consumers:
- `fuu.c()` (`EmailDataHandler`) adds device account email/name strings to the email language-model input list.
- `cyv.run()` discriminator 2 builds an account-email list and calls `fuu.e(...)`, which updates the Delight5 email LM.

Privacy assessment: **REMOVE account-derived seeding.** Keep the email LM and local personalization pipeline, but remove the device-account enumeration source. This preserves the feature while preventing Meboard from associating itself with accounts installed on the phone.

### `exg.iM()` discriminator 19 + `hyc.run()` discriminator 3 — Mozc self-account import

`iah` (`MozcInputMethodEntryActivationContentObserver`) creates `exg(context, 0x13)`.

The corresponding `exg` branch constructs an `irh` holding:
- `AccountManager.get(context)`
- a `MozcUserDictionaryImporter` (`ibw`)

`hyc` discriminator 3 then:
- calls `AccountManager.getAccounts()`
- maps every `Account.name`
- creates Mozc person-name entries
- writes them into user-dictionary group `__auto_imported_self_accounts` with category `人名`.

Privacy assessment: **REMOVE only self-account auto-import.** Preserve Mozc/Japanese IME, user dictionaries, and manually/local learned names. Delete the AccountManager provider branch and the runnable branch that imports installed account names.

### `mph` — AccountsStatusCheckerModule

Source marker: `com/google/android/libraries/inputmethod/accounts/checker/AccountsStatusCheckerModule`.

Direct AccountManager behavior:
- stores `AccountManager.get(context)`
- registers `OnAccountsUpdateListener` on module create
- refreshes status whenever Android accounts change
- unregisters listener on module destroy

The listener implementation is `moz`, whose `onAccountsUpdated()` calls `mph.a()` to refresh account state.

The module also queries account information through Google auth client code (`ktb`) rather than only through AccountManager. It maintains:
- all visible accounts
- `dasherAccounts`
- `griffinAccounts`
- `unicornAccounts`
- suppressed accounts
- whether a `@google.com` account exists
- `.edu` account classification
- AOC capability state
- adult capability state
- estimated age range

External consumers are primarily metrics/account-status plumbing:
- `evm` = `LatinMetricsProcessor`
- `nlq` via `nlo` = DailyPing processor/provider
- `AccountsCapabilitiesChangedReceiver`

`evm` and `nlq` copy account-derived booleans/age-range state into their metrics protobuf/state.

Privacy assessment: **REMOVE the entire account-status module and receiver graph.** It is account/metrics infrastructure, not required for local keyboard inference. Any user-facing feature that was gated by account capability should receive a signed-out/anonymous feature-safe decision through a separate local policy rather than retaining account discovery.

### `unb(Context)` — discarded AccountManager acquisition

Constructor calls `AccountManager.get(context)` and discards the returned manager. One observed construction occurs in the Mobile Data Download dependency graph (`pli`).

Privacy assessment: **REMOVE the AccountManager acquisition call.** Do not delete MDD/download functionality. This is a dependency/sanity hook, not a reason for a download subsystem to discover accounts.

## 2. Account discovery that bypasses AccountManager

Removing only `AccountManager` is insufficient.

### `ksg.a(Context)` — GoogleAuthUtil / GMS auth-account provider

Source/log marker: `GoogleAuthUtil`.

Behavior:
- connects to `com.google.android.gms.auth.accounts`
- invokes provider operation `get_accounts`
- asks for account type `com.google`
- returns `android.accounts.Account[]`

It also references GMS auth component `com.google.android.gms.auth.GetToken`.

### `mpo.b(Context)` — AndroidAccountUtils.getGoogleAccounts

Source marker: `com/google/android/libraries/inputmethod/accounts/utils/AndroidAccountUtils`.

Behavior:
- first tries the newer Google auth client (`ktb` / GoogleAuthClientWrapper)
- falls back to `ksg.a(Context)` / GoogleAuthUtil
- returns actual Google accounts from the device

`mpo.a(Context)` then tests whether any discovered account ends in `@google.com`.

Consumers:
- `evm` (`LatinMetricsProcessor`) — account classification in metrics
- `nlq` (DailyPing processor) — account classification in periodic metrics
- `rzb.i(...)` — may select the **first Google account name** as request/help identity

Privacy assessment: **REMOVE `mpo`/`ksg` account discovery after their account consumers are cut.** This is the primary bypass that would defeat an AccountManager-only patch.

## 3. Feedback / Google Help identity path

`rzb.i(Context, anonymous, ...)` constructs request/help context (`lfd`).

Behavior:
- when anonymous mode is true, identity string is literally `anonymous`
- otherwise calls `mpo.b(Context)`
- if accounts exist, takes account index 0 and stores `Account.name` as request/help identity

Observed consumers include:
- Rate Us / Google Help
- writing-helper thumbs-down feedback
- Jarvis / conversational writing feedback
- Agentic Dictation feedback
- SignBoard feedback
- QualityBugReporter / decoder report feedback
- other Google Help builders

Privacy assessment: **force this family onto its already-existing anonymous path by physically deleting the account-selection branch.** Preserve feedback/help UI and user-triggered reports, but never attach a device Google account identity.

## 4. Account capability broadcast receiver

`AccountsCapabilitiesChangedReceiver` listens for:
`com.google.android.gms.auth.ACCOUNT_CAPABILITIES_CHANGED`

It validates the sender as `com.google.android.gms`, resolves `mox` / AccountsStatusCheckerModule, and triggers account-status refresh.

Privacy assessment: **remove receiver registration and implementation with the account-status subsystem.** Meboard should not react to Google-account capability broadcasts.

## 5. Phenotype account-removal receiver

`com.google.android.libraries.phenotype.client.stable.AccountRemovedBroadcastReceiver` listens for:
`android.accounts.action.ACCOUNT_REMOVED`

It explicitly recognizes Google account types (`com.google`, `com.google.work`, `cn.google`) plus logged-out sentinel handling and feeds Phenotype state.

Privacy assessment: **remove with remote Phenotype infrastructure.** Remote Phenotype fetch/update removal is already a separate Meboard privacy layer; bundled/static flags may remain when needed for feature stability.

## 6. Manifest account surface

Original manifest includes:
- `android.permission.GET_ACCOUNTS`
- `AccountsCapabilitiesChangedReceiver`
- `Phenotype AccountRemovedBroadcastReceiver`
- GMS auth-account Phenotype registration metadata

Privacy assessment: **remove `GET_ACCOUNTS` and all account/capability/remote-Phenotype registrations once the code paths above are deleted.**

## 7. Important false positives — keep unless independently unnecessary

Not every `android.accounts.Account` reference means Meboard is reading the user's Google account.

### Mobstore/internal storage account namespace

`upg/upi/upj` use synthetic `Account` objects such as `shared` / type `mobstore` to encode storage paths and authorities. These are internal filesystem namespace objects, not Android AccountManager identities.

**Do not remove merely because they use the `Account` class.**

### Generic Google Play Services parcel/client classes

Classes such as GoogleHelp parcelables, generic Google API client request objects, and `GoogleSignInAccount` parcel readers may remain as shared library code even when no Meboard path discovers or supplies a real device account.

They should be judged by reachability and whether Meboard actually populates them with account identity, not by class name alone.

## Required Meboard end state

Static acceptance checks should report:

- zero `AccountManager.get(...)`
- zero `AccountManager.getAccounts()`
- zero account-update listener registration
- zero `GET_ACCOUNTS` permission
- zero GMS `get_accounts` provider calls
- zero `AndroidAccountUtils.getGoogleAccounts` reachable paths
- zero device-account auto-import into Email LM
- zero device-account auto-import into Mozc user dictionary
- zero account capability receiver/module
- zero Google-account identity injection into Help/Feedback
- remote Phenotype account-removal/update plumbing absent

Local email LM, local personalization, Mozc/Japanese IME, user dictionaries, local computation, local AI, downloads, dictation, and user-triggered anonymous online features should remain functional.
