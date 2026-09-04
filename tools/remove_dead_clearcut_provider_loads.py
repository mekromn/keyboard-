#!/usr/bin/env python3
"""Delete dead Clearcut provider reads left in retained feature factories.

Earlier feature-preserving surgery removed Lpqq constructor parameters from six
retained modules, leaving generated Dagger reads whose results are never used.
This script removes those reads physically and fails if the exact expected
Gboard 18.0.3 layout is not present.
"""
from pathlib import Path
import re

P = Path('/mnt/data/meboard_work/buildtree/smali/eqt.smali')
text = P.read_text()


def method(name: str, ret: str) -> tuple[int, int, str]:
    pat = re.compile(rf'(?ms)^\.method public final {re.escape(name)}\(\){re.escape(ret)}\n.*?^\.end method')
    m = pat.search(text)
    if not m:
        raise SystemExit(f'method {name}(){ret} not found')
    return m.start(), m.end(), m.group(0)


def rewrite(name: str, ret: str, pattern: str, expected_reg: str) -> None:
    global text
    a, b, body = method(name, ret)
    rx = re.compile(pattern, re.M | re.S)
    nb, n = rx.subn('', body, count=1)
    if n != 1:
        raise SystemExit(f'{name}: expected one dead Lpqq provider load, removed {n}')
    if f'check-cast {expected_reg}, Lpqq;' in nb:
        raise SystemExit(f'{name}: dead Lpqq cast remains')
    if '-><init>(Lpqq;' in nb or ';Lpqq;' in nb:
        raise SystemExit(f'{name}: an Lpqq constructor dependency still remains')
    text = text[:a] + nb + text[b:]
    print(f'{name}: removed dead Clearcut provider load')


rewrite(
    'P', 'Ljsj;',
    r'\n\s*\.line 1\n\s*iget-object v0, p0, Leqt;->l:Laals;.*?\n\s*check-cast v0, Lpqq;\n',
    'v0',
)
rewrite(
    'b', 'Lezc;',
    r'\n\s*\.line 5\n\s*iget-object v1, p0, Leqt;->l:Laals;.*?\n\s*check-cast v1, Lpqq;\n',
    'v1',
)
for name, ret in [('e', 'Lffw;'), ('f', 'Lfjz;'), ('i', 'Lfxg;')]:
    rewrite(
        name, ret,
        r'\n\s*\.line 17\n\s*\.line 18\n\s*iget-object p0, p0, Leqt;->l:Laals;.*?\n\s*check-cast p0, Lpqq;\n',
        'p0',
    )
rewrite(
    'h', 'Lfwn;',
    r'\n\s*\.line 4\n\s*\.line 5\n\s*iget-object p0, p0, Leqt;->l:Laals;.*?\n\s*check-cast p0, Lpqq;\n',
    'p0',
)

P.write_text(text)
print('all six dead Clearcut provider loads physically removed')
