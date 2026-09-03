#!/usr/bin/env python3
"""Delete the unreachable FeatureSplit metric module wrapper after stage-1 module pruning.

This is intentionally strict: the class is deleted only when no other class references it.
It exists solely to wrap the retired nwt/nwu metric module pair, which is removed next by
remove_dead_dagger_modules.py.
"""
from pathlib import Path
import re

ROOT = Path('/mnt/data/meboard_work/buildtree')
TARGET = 'nwv'

classes = {}
for p in ROOT.glob('smali*/**/*.smali'):
    t = p.read_text(errors='ignore')
    m = re.search(r'^\.class[^\n]* L([^;]+);', t, re.M)
    if m:
        classes[m.group(1)] = (p, t)

if TARGET not in classes:
    raise SystemExit(f'{TARGET} not found')
refs = [c for c, (_, t) in classes.items() if c != TARGET and f'L{TARGET};' in t]
if refs:
    raise SystemExit(f'{TARGET} unexpectedly referenced by {refs[:20]}')
classes[TARGET][0].unlink()
print(f'deleted unreachable {TARGET}')
