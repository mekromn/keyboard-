#!/usr/bin/env python3
"""Restore factory discriminator constants reused across removed registry slots.

Gboard's generated ``eqt.aI()`` module array builder reuses integer registers
between adjacent factory blocks. Physical deletion of telemetry-only slots 0xd3
and 0xf1 correctly removes their factories, but those blocks also initialized
constants consumed by the next retained factories. Smali still assembles when
the constants are lost, while runtime behavior changes (duplicate module keys or
wrong modules).

This pass restores only the two shared constants. It does not recreate either
removed module or any telemetry implementation.
"""
from pathlib import Path
import re

P = Path('/mnt/data/meboard_work/buildtree/smali/eqt.smali')
text = P.read_text()

repairs = [
    (
        'nwo discriminator 2 formerly initialized by removed qtc slot 0xd3',
        r'(const/16 v6, 0xd2\n\n'
        r'    const/16 v23, 0x[0-9a-f]+\n\n'
        r'    aput-object v4, v11, v23\n\n'
        r'    new-instance v4, Lnwo;\n\n)'
        r'(    invoke-direct \{v4, v12\}, Lnwo;-><init>\(I\)V\n\n'
        r'    const/16 v6, 0xd4)',
        r'\1    const/4 v12, 0x2\n\n\2',
    ),
    (
        'hyy discriminator 19 formerly initialized by removed qtc slot 0xf1',
        r'(const/16 v12, 0xf2\n\n'
        r'    const/16 v23, 0x[0-9a-f]+\n\n'
        r'    aput-object v4, v11, v23\n\n'
        r'    new-instance v4, Lhyy;\n\n)'
        r'(    invoke-direct \{v4, v6\}, Lhyy;-><init>\(I\)V\n\n'
        r'    const/16 v6, 0xf3)',
        r'\1    const/16 v6, 0x13\n\n\2',
    ),
]

for description, pattern, replacement in repairs:
    text, count = re.subn(pattern, replacement, text, count=1)
    if count != 1:
        raise SystemExit(f'{description}: expected one repair site, found {count}')
    print('restored', description)

P.write_text(text)

checks = [
    r'new-instance v4, Lnwo;\n\n    const/4 v12, 0x2\n\n'
    r'    invoke-direct \{v4, v12\}, Lnwo;-><init>\(I\)V',
    r'new-instance v4, Lhyy;\n\n    const/16 v6, 0x13\n\n'
    r'    invoke-direct \{v4, v6\}, Lhyy;-><init>\(I\)V',
]
for pattern in checks:
    if len(re.findall(pattern, text)) != 1:
        raise SystemExit(f'repaired registry sequence missing or duplicated: {pattern}')

print('eqt retained-factory discriminator semantics repaired')
