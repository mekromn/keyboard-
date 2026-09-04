#!/usr/bin/env python3
"""Replay the verified Meboard pipeline through stage 09.

The base replay reconstructs through Latin5 metrics removal. This continuation
then removes the detached expression metrics island and 23 additional metrics
processor/helper pairs, and emits a validated unsigned checkpoint APK.
"""
from pathlib import Path
import hashlib
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
WORK = Path('/mnt/data/meboard_work')
APKTOOL = Path('/mnt/data/meboard_tools/android/apktool/apktool.jar')
AAPT2 = Path('/mnt/data/meboard_tools/android/build-tools/aapt2')
OUTPUT = WORK / 'checkpoints' / 'Meboard-09-orphan-metrics-pairs-unsigned.apk'


def run(*args):
    command = [str(item) for item in args]
    print('+', ' '.join(command), flush=True)
    subprocess.run(command, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


run(sys.executable, ROOT / 'replay_meboard_pipeline.py', '--no-checkpoints')
run(sys.executable, ROOT / 'remove_expression_metrics_island.py')
run(sys.executable, ROOT / 'remove_orphan_metrics_pairs.py')
run(
    'java', '-jar', APKTOOL, 'b', '--aapt', AAPT2,
    '-f', '-j', '4', '-o', OUTPUT, WORK / 'buildtree'
)
with zipfile.ZipFile(OUTPUT) as archive:
    bad = archive.testzip()
    if bad:
        raise SystemExit(f'corrupt APK member: {bad}')
    dex = sorted(
        name for name in archive.namelist()
        if name.startswith('classes') and name.endswith('.dex')
    )
    if dex != ['classes.dex', 'classes2.dex', 'classes3.dex', 'classes4.dex']:
        raise SystemExit(f'unexpected DEX set: {dex}')
print(
    f'STAGE 09 COMPLETE: {OUTPUT} '
    f'({OUTPUT.stat().st_size} bytes; sha256={sha256(OUTPUT)})'
)
