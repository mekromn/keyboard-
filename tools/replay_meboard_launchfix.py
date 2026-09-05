#!/usr/bin/env python3
"""Replay Meboard through the first independently signed launchable checkpoint.

This runs the full stage-16 privacy-removal chain, then physically removes the
upstream Google-certificate whitelist that crashes legitimate independently
signed Meboard packages. The resulting APK is unsigned for final alignment and
stable-key signing.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = Path('/mnt/data/meboard_work')
APKTOOL = Path('/mnt/data/meboard_tools/android/apktool/apktool.jar')
AAPT2 = Path('/mnt/data/meboard_tools/android/build-tools/aapt2')
OUTPUT = WORK / 'checkpoints' / 'Meboard-launchfix-unsigned.apk'


def run(*args: str | Path) -> None:
    command = [str(item) for item in args]
    print('+', ' '.join(command), flush=True)
    subprocess.run(command, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    required = [
        ROOT / 'replay_meboard_stage16.py',
        ROOT / 'remove_signature_whitelist_guard.py',
        ROOT / 'verify_eqt_registry_registers.py',
        ROOT / 'verify_latinapp_context_register.py',
        ROOT / 'restore_density_split_resource_ids.py',
        ROOT / 'verify_density_split_resource_ids.py',
        APKTOOL,
        AAPT2,
    ]
    for path in required:
        if not path.is_file():
            raise SystemExit(f'missing replay input/tool: {path}')

    run(sys.executable, ROOT / 'replay_meboard_stage16.py')
    run(sys.executable, ROOT / 'remove_signature_whitelist_guard.py')
    run(sys.executable, ROOT / 'verify_eqt_registry_registers.py')
    run(sys.executable, ROOT / 'verify_latinapp_context_register.py')
    run(sys.executable, ROOT / 'restore_density_split_resource_ids.py')
    run(
        'java', '-jar', APKTOOL, 'b', '--aapt', AAPT2,
        '-f', '-j', '4', '-o', OUTPUT, WORK / 'buildtree',
    )

    run(sys.executable, ROOT / 'verify_density_split_resource_ids.py', OUTPUT)

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
        for name in dex:
            data = archive.read(name)
            for forbidden in (
                b'APK is signed by unrecognized certificates:',
                b'signature_check_security_exception_crash',
            ):
                # The preference/diagnostic flag may still exist in unrelated
                # generated flag metadata. The executable exception string may not.
                if forbidden.startswith(b'APK is signed') and forbidden in data:
                    raise SystemExit(f'executable signature-crash marker remains in {name}')

    print(
        f'LAUNCHFIX COMPLETE: {OUTPUT} '
        f'({OUTPUT.stat().st_size} bytes; sha256={sha256(OUTPUT)})'
    )


if __name__ == '__main__':
    main()
