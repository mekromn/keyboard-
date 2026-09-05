# Redundant checkpoint policy

Every Meboard stage is provisional until it has been saved and verified on three independent persistence surfaces.

## Required copies

1. **GitHub source checkpoint** — complete replay/patch scripts, verification gates, a human-readable report, and a machine-readable state manifest committed to a named ref. The public repository must never contain the proprietary source bundle, rebuilt APKs, signing key, key password, or other private signing material.
2. **Local immutable checkpoint** — a new timestamped directory containing real byte-for-byte copies of all required inputs and outputs. Hard links do not count. Every copy must be re-hashed after it is written.
3. **External user-owned checkpoint** — exported recovery archives copied to the user's persistent file Library or downloaded and stored outside the active runtime. A second pathname on the same filesystem is only a temporary mirror, not the final external copy.

## Public/private split

Each checkpoint produces two archives:

- `PUBLIC.zip`: replay scripts, audit reports, build logs, state manifests, hashes, and non-secret tooling.
- `PRIVATE.zip`: the complete recovery set, including the public material plus the original bundle, verified APK checkpoints, and the private signing archive.

The private archive is never committed to this public repository. The signing archive is kept separate inside the private section and is never unpacked into a public checkpoint.

## Acceptance gate for a stage

A numbered stage may be called complete only when all of the following exist:

- exact parent/input SHA-256 values;
- committed replay or migration script;
- immutable decoded-tree or clean-replay route;
- successful four-DEX rebuild;
- ZIP integrity pass;
- unsigned/aligned/signed APK hashes as applicable;
- signer-certificate fingerprint and update-signature continuity check;
- module-registry order and constructor/discriminator verification;
- physical-removal/privacy gate results;
- a report that distinguishes static verification from device testing;
- local checkpoint, archive mirror, GitHub commit, and external user-owned copy.

A historical log line or remembered hash does not prove that an artifact survived. If the file is missing, the stage is a reconstruction target and must be rebuilt and reverified. An older APK must never be relabeled as a later stage.

## Mutation and rollback rules

- Never overwrite a verified checkpoint.
- Build the next stage in a fresh worktree derived from the previous verified checkpoint or from a clean deterministic replay.
- Keep at least the previous two verified APK checkpoints, the untouched source bundle, the current replay kit, and the signing archive.
- On any verifier or build failure, discard the candidate worktree and retain the parent checkpoint unchanged.
- Mixed functional/metrics classes require branch-level review. Keyword matches alone are not deletion authority.

## Current recovery anchor

The checkpoint captured at `20260904T231709Z` records GitHub commit `1fba36df0b0187b51b4642ef307a9ad59c40895f`. At capture time, the highest APK physically present was the Stage-16 signature-guard-fix APK. Stage 18B's previously reported hash is retained only as a reconstruction comparison target because its APK and decoded tree were not present.