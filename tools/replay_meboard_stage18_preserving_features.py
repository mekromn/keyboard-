#!/usr/bin/env python3
"""Replay the tested Meboard baseline plus safe Stage-18 reporting cuts.

Order matters:
1. Reconstruct the working Stage-16 density-resource build from the untouched
   Gboard bundle.
2. Restore local-computation and explicit anonymous-feedback entry points that
   the broad Stage-1 manifest cut removed.
3. Remove the dedicated Mozc/Japanese reporting graph while retaining Japanese
   conversion, candidates, dictionaries, transliteration, rendering, local
   learning, handwriting, GenAI, and the mixed Undo listener.
4. Run register, resource, manifest, and package gates before producing output.

This script deliberately does not modify libintegrated_shared_object.so. Native
removal requires stronger indirect-call/relocation proof than the current binary
analysis provides; silently zeroing or stubbing functions would violate both the
physical-removal and feature-preservation policies.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = Path('/mnt/data/meboard_work')
APKTOOL = Path('/mnt/data/meboard_tools/android/apktool/apktool.jar')
AAPT2 = Path('/mnt/data/meboard_tools/android/build-tools/aapt2')
OUTPUT = WORK / 'checkpoints/Meboard-stage18-safe-unsigned.apk'


def run(*args: str | Path) -> None:
    command = [str(x) for x in args]
    print('+', ' '.join(command), flush=True)
    subprocess.run(command, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def classes() -> set[str]:
    result: set[str] = set()
    rx = re.compile(r'^\.class[^\n]* L([^;]+);', re.M)
    for path in (WORK / 'buildtree').glob('smali*/**/*.smali'):
        match = rx.search(path.read_text(errors='ignore'))
        if match:
            result.add(match.group(1))
    return result


def main() -> None:
    required = (
        'replay_meboard_launchfix.py',
        'restore_retained_manifest_entrypoints.py',
        'remove_mozc_telemetry_complete.py',
        'verify_eqt_registry_registers.py',
        'verify_latinapp_context_register.py',
        'verify_density_split_resource_ids.py',
    )
    for name in required:
        path = HERE / name
        if not path.is_file():
            raise SystemExit(f'missing replay stage: {path}')
    for path in (APKTOOL, AAPT2):
        if not path.is_file():
            raise SystemExit(f'missing Android build tool: {path}')

    run(sys.executable, HERE / 'replay_meboard_launchfix.py')
    before = classes()
    run(sys.executable, HERE / 'restore_retained_manifest_entrypoints.py')
    run(sys.executable, HERE / 'remove_mozc_telemetry_complete.py')
    after = classes()
    deleted = sorted(before - after)
    if not 5 <= len(deleted) <= 24:
        raise SystemExit(
            f'refusing unexpected Mozc reporting delta: {len(deleted)} classes: {deleted}'
        )

    # No retained class may still reference a deleted descriptor.
    dangling: list[tuple[str, str]] = []
    for path in (WORK / 'buildtree').glob('smali*/**/*.smali'):
        text = path.read_text(errors='ignore')
        for descriptor in deleted:
            if f'L{descriptor};' in text:
                dangling.append((str(path), descriptor))
    if dangling:
        raise SystemExit(f'dangling Mozc reporting references: {dangling[:50]}')

    run(sys.executable, HERE / 'verify_eqt_registry_registers.py')
    run(sys.executable, HERE / 'verify_latinapp_context_register.py')
    run(
        'java', '-jar', APKTOOL, 'b', '--aapt', AAPT2,
        '-f', '-j', '4', '-o', OUTPUT, WORK / 'buildtree',
    )
    run(sys.executable, HERE / 'verify_density_split_resource_ids.py', OUTPUT)

    with zipfile.ZipFile(OUTPUT) as archive:
        bad = archive.testzip()
        if bad:
            raise SystemExit(f'corrupt APK member: {bad}')
        dex = sorted(
            name for name in archive.namelist()
            if name.startswith('classes') and name.endswith('.dex')
        )
        expected = ['classes.dex', 'classes2.dex', 'classes3.dex', 'classes4.dex']
        if dex != expected:
            raise SystemExit(f'unexpected DEX set: {dex}')

    print('Stage-18 safe reporting build complete')
    print('Deleted Mozc reporting classes:', deleted)
    print('Output:', OUTPUT)
    print('SHA-256:', sha256(OUTPUT))


if __name__ == '__main__':
    main()
