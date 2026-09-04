#!/usr/bin/env python3
"""Replay the verified Meboard privacy pipeline through stage 16.

Stage 16 includes the stage-12 base removals plus detached feature/Latin metrics,
Jarvis prompt metrics, hidden Keyhound collection/export removal, the Meboard
stable-signer runtime adaptation, and restoration of fused density resources.
The result remains unsigned for static audit and later native/network verification.
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
OUTPUT = WORK / 'checkpoints' / 'Meboard-stage16-keyhound-removed-unsigned.apk'

CONTINUATION = [
    'remove_expression_metrics_island.py',
    'remove_orphan_metrics_pairs.py',
    'remove_closed_metrics_clusters.py',
    'remove_gqn_clearcut_wrapper.py',
    'remove_training_cache_processors.py',
    'remove_detached_feature_metrics.py',
    'remove_detached_latin_metrics.py',
    'remove_jarvis_metrics_processors.py',
    'remove_keyhound_collection_module.py',
    'fix_runtime_identity_and_split_resources.py',
]


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
        ROOT / 'replay_meboard_pipeline.py',
        ROOT / 'verify_eqt_registry_registers.py',
        ROOT / 'verify_module_registry_subsequence.py',
        ROOT / 'repair_eqt_reused_discriminators.py',
        *(ROOT / name for name in CONTINUATION),
        APKTOOL,
        AAPT2,
    ]
    for path in required:
        if not path.is_file():
            raise SystemExit(f'missing replay input/tool: {path}')

    run(sys.executable, ROOT / 'replay_meboard_pipeline.py', '--no-checkpoints')
    for script in CONTINUATION:
        run(sys.executable, ROOT / script)

    # Some removed registry providers also initialized discriminator registers
    # consumed by the immediately following retained providers. Restore only
    # those shared constants after all stage-16 registry compaction is complete.
    run(sys.executable, ROOT / 'repair_eqt_reused_discriminators.py')

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    run(sys.executable, ROOT / 'verify_eqt_registry_registers.py')
    run(sys.executable, ROOT / 'verify_module_registry_subsequence.py')
    run(
        'java', '-jar', APKTOOL, 'b', '--aapt', AAPT2,
        '-f', '-j', '4', '-o', OUTPUT, WORK / 'buildtree',
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
        f'STAGE 16 COMPLETE: {OUTPUT} '
        f'({OUTPUT.stat().st_size} bytes; sha256={sha256(OUTPUT)})'
    )


if __name__ == '__main__':
    main()
