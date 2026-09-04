#!/usr/bin/env python3
"""Replay the verified Meboard privacy pipeline through stage 13.

Stages 08-13 remove the expression metrics island, orphan processor/helper
pairs, closed Writing Tools/Latin metrics clusters, the detached Clearcut
forwarder, Java training-cache exporters, and the detached Undo/FreeCursor/
companion-widget metrics islands. The final APK remains unsigned for audit.
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
OUTPUT = WORK / 'checkpoints' / 'Meboard-13-detached-feature-metrics-unsigned.apk'

CONTINUATION = [
    'remove_expression_metrics_island.py',
    'remove_orphan_metrics_pairs.py',
    'remove_closed_metrics_clusters.py',
    'remove_gqn_clearcut_wrapper.py',
    'remove_training_cache_processors.py',
    'remove_detached_feature_metrics.py',
]


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


for required in [
    ROOT / 'replay_meboard_pipeline.py',
    *(ROOT / name for name in CONTINUATION),
    APKTOOL,
    AAPT2,
]:
    if not required.is_file():
        raise SystemExit(f'missing replay input/tool: {required}')

run(sys.executable, ROOT / 'replay_meboard_pipeline.py', '--no-checkpoints')
for script in CONTINUATION:
    run(sys.executable, ROOT / script)
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
    expected = ['classes.dex', 'classes2.dex', 'classes3.dex', 'classes4.dex']
    if dex != expected:
        raise SystemExit(f'unexpected DEX set: {dex}')
print(
    f'STAGE 13 COMPLETE: {OUTPUT} '
    f'({OUTPUT.stat().st_size} bytes; sha256={sha256(OUTPUT)})'
)
