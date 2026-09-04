#!/usr/bin/env python3
"""Restore two retained factory discriminator constants lost with removed slots.

Gboard's generated ``eqt.aI()`` builder reuses integer registers between module
factory blocks. Removing telemetry-only qtc slots 0xd3 and 0xf1 also removes the
constant assignments consumed by the immediately following retained factories.
The compacted Meboard registry inserts its own v23 array-index assignment between
those blocks, so this pass identifies the retained factories by their original
neighbouring *module-slot* constants rather than by brittle blank-line layout.

Only the original nwo(2) and hyy(19) constructor arguments are restored. No
removed provider, module, registration, or telemetry implementation is recreated.
"""
from __future__ import annotations

import re
from pathlib import Path

P = Path('/mnt/data/meboard_work/buildtree/smali/eqt.smali')
text = P.read_text()

repairs = [
    (
        'nwo discriminator 2 formerly initialized by removed qtc slot 0xd3',
        re.compile(
            r'(?ms)('
            r'    const/16 v6, 0xd2\n\n'
            r'    const/16 v23, 0x[0-9a-f]+\n'
            r'    aput-object v4, v11, v23\n\n'
            r'(?:\s*\n)*'
            r'    new-instance v4, Lnwo;\n\n'
            r')('
            r'    invoke-direct \{v4, v12\}, Lnwo;-><init>\(I\)V\n\n'
            r'    const/16 v6, 0xd4'
            r')'
        ),
        r'\1    const/4 v12, 0x2\n\n\2',
    ),
    (
        'hyy discriminator 19 formerly initialized by removed qtc slot 0xf1',
        re.compile(
            r'(?ms)('
            r'    const/16 v12, 0xf2\n\n'
            r'    const/16 v23, 0x[0-9a-f]+\n'
            r'    aput-object v4, v11, v23\n\n'
            r'(?:\s*\n)*'
            r'    new-instance v4, Lhyy;\n\n'
            r')('
            r'    invoke-direct \{v4, v6\}, Lhyy;-><init>\(I\)V\n\n'
            r'    const/16 v6, 0xf3'
            r')'
        ),
        r'\1    const/16 v6, 0x13\n\n\2',
    ),
]

for description, pattern, replacement in repairs:
    text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise SystemExit(f'{description}: expected one semantic repair site, found {count}')
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
