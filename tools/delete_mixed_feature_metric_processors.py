#!/usr/bin/env python3
from pathlib import Path
import re
R=Path('/mnt/data/meboard_work/buildtree')
groups=[['fga','fgb','pqg'],['flb','flc'],['fda','fdb'],['ezi','ezj'],['fwp','fwq'],['fxk','fxl'],['jsx','jsy']]
D={c for g in groups for c in g}
classes={}
for p in R.glob('smali*/**/*.smali'):
    t=p.read_text(errors='ignore');m=re.search(r'^\.class[^\n]* L([^;]+);',t,re.M)
    if m: classes[m.group(1)]=(p,t)
for c in D:
    if c not in classes: raise SystemExit(f'missing {c}')
    ext=[x for x,(_,t) in classes.items() if x not in D and f'L{c};' in t]
    if ext: raise SystemExit(f'{c} external refs: {ext[:30]}')
for c in sorted(D): classes[c][0].unlink(); print('deleted',c)
print('deleted mixed-feature telemetry implementations; feature modules retained')
