#!/usr/bin/env python3
"""Restore split-backed resources required by the monolithic Meboard APK.

The original Gboard bundle resolves several drawable references from the xxhdpi
split at install time. Meboard fuses that split into a standalone APK, while
Apktool initially decodes the temporarily absent references as ``@null``.

Certificate-whitelist removal deliberately does *not* live in this stage. The
later ``remove_signature_whitelist_guard.py`` pass owns the producer, shared
Runnable branch, comparator, and embedded digest removal as one atomic physical
excision. Keeping these responsibilities separate makes stage 16 independently
replayable and prevents a partial/no-op signature patch from satisfying the
physical-removal policy.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path('/mnt/data/meboard_work/buildtree')


def replace_nulls(path: Path, targets: list[str]) -> None:
    text = path.read_text()
    if text.count('@null') != len(targets):
        raise SystemExit(
            f'{path.name}: expected {len(targets)} unresolved split references, '
            f'found {text.count("@null")}'
        )
    for target in targets:
        target_name = f'APKTOOL_RENAMED_0x{target}'
        candidates = list((ROOT / 'res').glob(f'drawable*/{target_name}.*'))
        if not candidates:
            raise SystemExit(f'{path.name}: fused target drawable {target_name} is missing')
        text = text.replace('@null', f'@drawable/{target_name}', 1)
    path.write_text(text)
    print(f'{path.name}: restored {len(targets)} split-backed drawable reference(s)')


def restore_split_references() -> None:
    drawable = ROOT / 'res' / 'drawable'
    fixes = {
        # Bitmap wrappers.
        'APKTOOL_RENAMED_0x7f080581.xml': ['7f080580'],
        'APKTOOL_RENAMED_0x7f0805dc.xml': ['7f0805dd'],
        'APKTOOL_RENAMED_0x7f0805e0.xml': ['7f0805e1'],
        'APKTOOL_RENAMED_0x7f0805e3.xml': ['7f08060d'],
        'APKTOOL_RENAMED_0x7f0805e7.xml': ['7f0805e8'],
        # Required nine-patch/bitmap selector children, in XML document order.
        'APKTOOL_RENAMED_0x7f08020e.xml': ['7f080244', '7f080244', '7f080243'],
        'APKTOOL_RENAMED_0x7f080234.xml': [
            '7f08022f', '7f08022f', '7f080231', '7f080230'
        ],
    }
    for filename, targets in fixes.items():
        path = drawable / filename
        if not path.is_file():
            raise SystemExit(f'missing split-reference wrapper: {path}')
        replace_nulls(path, targets)

    invalid: list[str] = []
    required_src = re.compile(r'<(?:bitmap|nine-patch)\b[^>]*android:src="@null"')
    for path in (ROOT / 'res').rglob('*.xml'):
        if required_src.search(path.read_text(errors='ignore')):
            invalid.append(str(path.relative_to(ROOT)))
    if invalid:
        raise SystemExit(f'required drawable src still resolves to @null: {invalid}')
    print('all required bitmap/nine-patch sources resolve to fused density assets')


def main() -> None:
    restore_split_references()


if __name__ == '__main__':
    main()
