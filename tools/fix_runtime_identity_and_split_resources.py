#!/usr/bin/env python3
"""Make the re-signed monolithic Meboard runtime-safe.

The original Gboard bundle assumes Google's production signing certificates and
resolves several drawable references from the xxhdpi split at install time. A
standalone Meboard APK intentionally has a different stable signer and fuses the
split resources into the base APK. This pass therefore:

1. physically removes the Google-only self-signature failure branch; and
2. restores resource-ID references that Apktool decoded as ``@null`` while the
   density split was temporarily absent.

The pass is assertion-heavy and targets only Gboard 18.0.3.954559732 arm64.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path('/mnt/data/meboard_work/buildtree')


def remove_google_signature_gate() -> None:
    path = ROOT / 'smali' / 'mm.smali'
    text = path.read_text()
    pattern = re.compile(r'(?ms)^    :pswitch_b\n.*?(?=^    :pswitch_c\n)')
    match = pattern.search(text)
    if not match:
        raise SystemExit('mm.run signature-check switch branch not found')
    block = match.group(0)
    required = [
        'Lrpv;->a(Landroid/content/Context;Ljava/lang/String;)Z',
        'APK is signed by unrecognized certificates:',
        'Ljava/lang/IllegalStateException;',
    ]
    missing = [needle for needle in required if needle not in block]
    if missing:
        raise SystemExit(f'mm.run pswitch_b is not the expected signature gate: {missing}')
    replacement = (
        '    :pswitch_b\n'
        '    # Google production-certificate allowlist removed for the independently\n'
        '    # signed Meboard coexistence package.\n'
        '    return-void\n\n'
    )
    text = text[:match.start()] + replacement + text[match.end():]
    for needle in required:
        if needle in text:
            raise SystemExit(f'signature-gate implementation remains after removal: {needle}')
    path.write_text(text)
    print('mm.run: physically removed Google-only certificate rejection branch')


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
    remove_google_signature_gate()
    restore_split_references()


if __name__ == '__main__':
    main()
