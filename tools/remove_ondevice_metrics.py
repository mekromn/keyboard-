#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path('/mnt/data/meboard_work/buildtree')
PROC='com/google/android/libraries/inputmethod/ondevicemetricaggregation/OnDeviceMetricAggregationProcessor'

def find_desc(c):
    name=c.split('/')[-1]+'.smali'
    hits=[]
    for p in ROOT.glob('smali*/**/'+name):
        t=p.read_text(errors='ignore')
        if re.search(rf'^\.class[^\n]* L{re.escape(c)};',t,re.M): hits.append(p)
    if len(hits)!=1: raise SystemExit(f'{c}: {hits}')
    return hits[0]
eq=find_desc('eqt'); s=eq.read_text()
s,n=re.subn(r'(?ms)^\.method public final ak\(\)Lpzz;\n.*?^\.end method\n?','',s,count=1)
if n!=1: raise SystemExit('eqt ak()Lpzz not found')
s,n=re.subn(r'(?m)^\.implements Lqaa;\n','',s,count=1)
if n!=1: raise SystemExit('eqt Lqaa not found')
eq.write_text(s)
nrn=find_desc('nrn'); s=nrn.read_text()
needle=f'    sget p0, L{PROC};->l:I\n\n'
if needle not in s: raise SystemExit('nrn processor anchor not found')
s=s.replace(needle,'',1)
nrn.write_text(s)
for c in ['pzv','qaa','pzz','pzw','pzt','pzu',PROC,'pzx']:
    p=find_desc(c); p.unlink(); print('deleted',c)
for c in ['pzv','qaa','pzz','pzw','pzt','pzu',PROC,'pzx']:
    hits=[]
    for p in ROOT.glob('smali*/**/*.smali'):
        if f'L{c};' in p.read_text(errors='ignore'): hits.append(str(p.relative_to(ROOT)))
    if hits: raise SystemExit(f'{c} dangling refs {hits[:20]}')
print('on-device metric aggregation implementation physically removed')
