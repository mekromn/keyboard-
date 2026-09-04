#!/usr/bin/env python3
"""Reconstruct the current Meboard privacy tree deterministically.

The individual surgical patches intentionally contain strict assertions for the
exact Gboard 18.0.3.954559732 arm64 layout. This driver supplies their actual
dependency order, recreates the decoded inputs from the original ASPK, rebuilds
at checkpoints, and aborts on the first mismatch.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

WORK = Path('/mnt/data/meboard_work')
DEFAULT_BUNDLE = Path('/mnt/data/Gboard_175940518_18.0.3.954559732-release-arm64-v8a.aspk')
DEFAULT_APKTOOL = Path('/mnt/data/meboard_tools/android/apktool/apktool.jar')
DEFAULT_AAPT2 = Path('/mnt/data/meboard_tools/android/build-tools/aapt2')
TOOLS = Path(__file__).resolve().parent

# Backfilled orphan cleanups must run before the broader removers that assert
# no dangling references. Account isolation precedes the final Cronet assertion.
PATCHES = [
    'prune_removed_provider_cases.py',
    'prune_aui_feedback.py',
    'remove_orphan_nwv.py',
    'remove_dead_dagger_modules.py',
    'remove_orphan_telemetry_wrappers.py',
    'remove_perfetto.py',
    'remove_ondevice_metrics.py',
    'remove_unreachable_components.py',
    'remove_training_guard_maintainer.py',
    'remove_training_metrics_clusters.py',
    'remove_primes_processor.py',
    'dce_eqt_setup.py',
    'remove_primes_flag_providers.py',
    'prune_rse_primes.py',
    'remove_remaining_primes.py',
    'remove_legacy_clearcut_adapter.py',
    'remove_remote_phenotype.py',
    'remove_dynamic_federated_trainer.py',
    'remove_account_identity_sources.py',
    'remove_native_federated_runner.py',
    'remove_account_receiver_outline.py',
    'remove_account_status_module.py',
    'remove_cronet_telemetry.py',
    'remove_primes_transport_metrics.py',
    'remove_primes_interceptor_branch.py',
    'strip_mixed_feature_metrics.py',
    'delete_mixed_feature_metric_processors.py',
    'remove_dead_clearcut_provider_loads.py',
    'remove_standalone_metrics_modules.py',
    'remove_handwriting_metrics_module.py',
    'remove_latin5_metrics_module.py',
]

CHECKPOINT_AFTER = {
    'remove_primes_processor.py': '01-core-metrics',
    'remove_legacy_clearcut_adapter.py': '02-primes-clearcut',
    'remove_cronet_telemetry.py': '03-account-network',
    'remove_dead_clearcut_provider_loads.py': '04-dead-clearcut-loads',
    'remove_standalone_metrics_modules.py': '05-standalone-metrics',
    'remove_handwriting_metrics_module.py': '06-handwriting-metrics',
    'remove_latin5_metrics_module.py': '07-latin5-metrics',
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def run(*args: str | Path, cwd: Path | None = None) -> None:
    cmd = [str(x) for x in args]
    print('+', ' '.join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def find_nested(root: Path, filename: str) -> Path:
    hits = list(root.rglob(filename))
    if len(hits) != 1:
        raise SystemExit(f'expected exactly one {filename}, found {len(hits)}: {hits}')
    return hits[0]


def decode(apktool: Path, apk: Path, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    run('java', '-jar', apktool, 'd', '-f', '-o', out, apk)


def build(apktool: Path, aapt2: Path, label: str) -> Path:
    run(sys.executable, TOOLS / 'verify_eqt_registry_registers.py')
    out = WORK / 'checkpoints' / f'Meboard-{label}-unsigned.apk'
    out.parent.mkdir(parents=True, exist_ok=True)
    run('java', '-jar', apktool, 'b', '--aapt', aapt2, '-f', '-j', '4', '-o', out, WORK / 'buildtree')
    with zipfile.ZipFile(out) as zf:
        bad = zf.testzip()
        if bad:
            raise SystemExit(f'{label}: corrupt ZIP member {bad}')
        dex = sorted(x for x in zf.namelist() if x.startswith('classes') and x.endswith('.dex'))
        if not dex:
            raise SystemExit(f'{label}: no DEX files in rebuilt APK')
    print(f'CHECKPOINT {label}: {out} ({out.stat().st_size} bytes; sha256={sha256(out)})')
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--bundle', type=Path, default=DEFAULT_BUNDLE)
    ap.add_argument('--apktool', type=Path, default=DEFAULT_APKTOOL)
    ap.add_argument('--aapt2', type=Path, default=DEFAULT_AAPT2)
    ap.add_argument('--no-checkpoints', action='store_true')
    args = ap.parse_args()

    for p in (args.bundle, args.apktool, args.aapt2):
        if not p.is_file():
            raise SystemExit(f'missing required input/tool: {p}')
    for name in ['patch_meboard_stage1.py', 'verify_eqt_registry_registers.py', *PATCHES]:
        if not (TOOLS / name).is_file():
            raise SystemExit(f'missing patch script: {TOOLS / name}')

    for d in ('input', 'decoded', 'buildtree', 'checkpoints'):
        path = WORK / d
        if path.exists():
            shutil.rmtree(path)
    (WORK / 'input').mkdir(parents=True)

    with zipfile.ZipFile(args.bundle) as zf:
        zf.extractall(WORK / 'input')
    base = find_nested(WORK / 'input', 'base.apk')
    density = find_nested(WORK / 'input', 'split_config.xxhdpi.apk')
    # Normalize nested-bundle locations expected by the surgical scripts.
    for src in list((WORK / 'input').rglob('*.apk')):
        dst = WORK / 'input' / src.name
        if src != dst:
            shutil.copy2(src, dst)

    decode(args.apktool, base, WORK / 'decoded' / 'base')
    decode(args.apktool, density, WORK / 'decoded' / 'density')
    run(sys.executable, TOOLS / 'patch_meboard_stage1.py')
    shutil.copytree(WORK / 'decoded' / 'base', WORK / 'buildtree')
    if not args.no_checkpoints:
        build(args.apktool, args.aapt2, '00-stage1')

    for script in PATCHES:
        run(sys.executable, TOOLS / script)
        if not args.no-checkpoints and script in CHECKPOINT_AFTER:
            build(args.apktool, args.aapt2, CHECKPOINT_AFTER[script])

    final = build(args.apktool, args.aapt2, 'current')
    print(f'REPLAY COMPLETE: {final}')


if __name__ == '__main__':
    main()
