# Gboard account buckets: Dasher, Griffin, Unicorn, and `suppressed`

Target: Gboard 18.0.3.954559732 arm64, decoded from the project owner's source bundle.

This document records the exact behavior of `AccountsStatusCheckerModule` (`mph`) and its `Accounts` snapshot class (`mow`).

## Exact snapshot layout

`mow.toString()` preserves the original Kotlin/data-class field names and maps the obfuscated fields exactly:

- `a` = `allAccounts`
- `b` = `dasherAccounts`
- `c` = `griffinAccounts`
- `d` = `unicornAccounts`
- `e` = `suppressed`
- `i` = `fetchId`
- `f` = derived boolean: whether any account email ends in `@google.com`

Each account object is `ksr`, containing:

- field `a`: obfuscated GAIA ID
- field `b`: Android/Google account type (used to reconstruct `android.accounts.Account`)
- field `c`: account email/name

`ksr.toString()` prints the email/name plus the obfuscated GAIA ID.

## How the lists are fetched

`AccountsStatusCheckerModule.d()` performs four account queries in sequence:

1. all visible `com.google` accounts with no feature filter
2. accounts filtered by `service_HOSTED`
3. accounts filtered by `service_hgp`
4. accounts filtered by `service_uca`

The resulting constructor mapping is exact:

- `allAccounts` <- no feature filter
- `dasherAccounts` <- `service_HOSTED`
- `griffinAccounts` <- `service_hgp`
- `unicornAccounts` <- `service_uca`
- `suppressed` <- caught feature-query exceptions

The query object requests account type `com.google`. Its `includeRestrictedAccounts` and `includeTransientAccounts` values are both false.

The code's own metric/error enum independently confirms the names:

- `GET_DASHER_ACCOUNTS_FAILED` / `GAC.GetAccounts.Dasher.Failed`
- `GET_GRIFFIN_ACCOUNTS_FAILED` / `GAC.GetAccounts.Griffin.Failed`
- `GET_UNICORN_ACCOUNTS_FAILED` / `GAC.GetAccounts.Unicorn.Failed`

## Dasher accounts

In this build, `dasherAccounts` are exactly the visible Google accounts carrying GAIA feature `service_HOSTED`.

Public Google/Chromium and court material use "Dasher" for enterprise/hosted Google accounts: organization-managed accounts such as Google Workspace accounts. The organization/enterprise administrator can control available Google services and policy/settings for these accounts.

Gboard additionally derives an `has edu account` tri-state from the Dasher list only. It checks Dasher account email strings against regex `@.+\\.edu(\\.|$)`.

Therefore, Gboard distinguishes:

- Dasher generally: managed/hosted enterprise account
- EDU Dasher specifically: Dasher account whose email matches the `.edu` regex

All Dasher accounts contribute to Gboard's `has managed account` result. Only EDU Dasher accounts contribute through the Dasher path to `has supervised account`.

## Griffin accounts

In this build, `griffinAccounts` are exactly visible Google accounts carrying GAIA feature `service_hgp`.

Public Chromium documentation describes a Griffin account as a Family Link / supervised child-user account type, similar to a Geller supervised account, but specifically used for compliance with European Union laws. Geller supervision itself has no age restriction; Griffin is the EU-compliance variant in Chromium's child-user taxonomy.

Within Gboard, any non-empty Griffin list contributes to both:

- `has managed account`
- `has supervised account`

No email-domain test is required for Griffin accounts.

## Unicorn accounts

In this build, `unicornAccounts` are exactly visible Google accounts carrying GAIA feature `service_uca`.

Chromium's Android account code explicitly names `service_uca` as the account feature indicating a child account. Chromium's user-type documentation describes a Unicorn account as an account designated for children under the age of consent in their jurisdiction. In the US this commonly corresponds to a Family Link child account created while the child is under 13, but the code/documentation uses jurisdictional age of consent rather than a universal age of 13.

Within Gboard, any non-empty Unicorn list contributes to both:

- `has managed account`
- `has supervised account`

## What `suppressed` really is

`suppressed` is **not a list of suppressed accounts**.

It is an `ArrayList` populated with `ksf` exceptions (`ksf extends java.lang.Exception`) caught while fetching the feature-filtered account lists. Gboard intentionally continues the overall account snapshot when a Dasher, Griffin, or Unicorn query fails, stores the exception in `suppressed`, and makes the failed category list `null`.

The diagnostic dumper iterates `suppressed` as `Throwable` objects and prints their stack traces. If empty, it prints `suppressed: []`.

This creates an important distinction:

- empty list = query succeeded and found no matching accounts
- non-empty list = query succeeded and found matching accounts
- `null` list = category could not be determined because its query failed
- `suppressed` = the failure(s) explaining those unknown results

## Derived tri-state account properties

`mow` does not collapse failed category lookups to false. It uses nullable `Boolean` results.

### `has edu account` (`mow.a()`)

- examines only `dasherAccounts`
- true if any Dasher email matches `@.+\\.edu(\\.|$)`
- false if Dasher query succeeded with no matching EDU address
- if Dasher classification is unavailable and there are Google accounts, result can be unknown (`null`)
- if there are no Google accounts at all, false

### Child/supervised-category presence (`mow.b()` internally)

- OR of non-empty `griffinAccounts` and `unicornAccounts`
- preserves unknown when feature lookup failed and accounts exist
- false when no Google accounts exist

### `has managed account` (`mow.c()`)

- tri-state OR of Dasher, Griffin, and Unicorn presence
- therefore any of the three types is considered "managed" by this Gboard subsystem

### `has supervised account` (`mow.d()`)

- tri-state OR of `has edu account` and Griffin/Unicorn presence
- so supervised means: EDU Dasher **or** Griffin **or** Unicorn

The module's diagnostic dumper labels these exact derived outputs as:

- `has edu account`
- `has managed account`
- `has supervised account`

## Other data derived from the account snapshot

The `Accounts` snapshot also computes whether any account email ends with `@google.com` (`mow.f`).

`AccountsStatusCheckerModule.b()` combines the account snapshot with separate capability queries (`HasAocCapability`, `HasAdultCapability`) to produce `AccountsWithEstimatedAgeRange` (`mpm`). The estimated age range is therefore account/capability-derived state layered on top of these bucket results.

LatinMetricsProcessor and DailyPing consume account-derived state from this subsystem, including the `@google.com` presence boolean and estimated-age-range value.

## Meboard privacy conclusion

These buckets are account classification/metrics/policy infrastructure, not local keyboard inference state. For Meboard's signed-out privacy model, the correct treatment is to remove account discovery and these classification queries rather than fake empty buckets while retaining account access.

Local language models, personalization, Japanese/Mozc, local computation, dictionaries, dictation, and user-triggered anonymous online features do not need these category lists themselves.