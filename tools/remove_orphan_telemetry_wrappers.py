#!/usr/bin/env python3
"""Physically delete module wrappers orphaned by telemetry implementation removal."""
from pathlib import Path
import re

ROOT = Path('/mnt/data/meboard_work/buildtree')
TARGETS = ['qbj', 'pzy', 'qjg']

classes = {}
for p in ROOT.glob('smali*/**/*.smali'):
    t = p.read_text(errors='ignore')
    m = re.search(r'^\.class[^\n]* L([^;]+);', t, re.M)
    if m:
        classes[m.group(1)] = (p, t)

for target in TARGETS:
    if target not in classes:
        raise SystemExit(f'{target} not found')
    refs = [c for c, (_, t) in classes.items() if c != target and f'L{target};' in t]
    if refs:
        raise SystemExit(f'{target} unexpectedly referenced by {refs[:20]}')
for target in TARGETS:
    classes[target][0].unlink()
    print(f'deleted unreachable telemetry wrapper {target}')
