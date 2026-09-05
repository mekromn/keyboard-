# Meboard — authoritative resume pointer

Checkpoint ID: `20260905T012006Z`

## Start here after any interruption

1. GitHub branch: `meboard/resume-latest` in `mekromn/keyboard-`.
2. Library folder: `/Meboard/Checkpoints/20260905T012006Z`.
3. Read `Meboard-stage16-launchfix-replay-verification.md`.
4. Candidate: `Meboard-stage16-launchfix-replay-signed.apk`.
5. Candidate SHA-256: `dd8044ae0c365d6e7fbc6a87295cedd6c06bcf87027cdda287b9b9ef8021ffb5`.
6. Stable signer certificate SHA-256: `23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15`.

## Current truth

- Clean replay: passed.
- Four DEX, v3 signing, and 16 KiB alignment: passed.
- Static retained-feature gate: passed.
- Full on-device IME/runtime gate: not run.
- Privacy completion: not complete.
- APKbox/device control: not used.

## Feature invariant

No user-facing Gboard functionality is an approved removal target. Preserve all keyboard features and useful local/on-device AI. Any privacy patch that breaks a retained feature is failed and must be corrected or rolled back.

## Next action

Manually install/update the candidate and test LatinIME bind/render/type/switch-away/switch-back. Do not modify this checkpoint APK. Continue privacy work from a new branch only after recording the runtime result.
