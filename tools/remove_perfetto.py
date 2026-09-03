#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path('/mnt/data/meboard_work/buildtree')

def find(c):
    hits=list(ROOT.glob(f'smali*/**/{c}.smali'))
    if len(hits)!=1: raise SystemExit(f'{c}: {hits}')
    return hits[0]
eq=find('eqt'); s=eq.read_text()
pat=re.compile(r'(?ms)^\.method public final al\(\)Lqbi;\n.*?^\.end method\n?')
s,n=pat.subn('',s,count=1)
if n!=1: raise SystemExit('eqt al()Lqbi not found')
s,n=re.subn(r'(?m)^\.implements Lqbk;\n','',s,count=1)
if n!=1: raise SystemExit('eqt Lqbk interface not found')
eq.write_text(s)
ouj=find('ouj'); s=ouj.read_text()
start=s.find('    sget-object v1, Lpsr;->h:Lpsr;\n')
if start<0: raise SystemExit('Perfetto timing branch start not found')
end=s.find('    :cond_7\n',start)
if end<0: raise SystemExit('Perfetto timing branch end not found')
s=s[:start]+s[end:]
ouj.write_text(s)
for c in ['qbf','qbk','qbi','qbg','qbh','qbl']:
    find(c).unlink(); print('deleted',c)
for c in ['qbf','qbk','qbi','qbg','qbh','qbl']:
    hits=[]
    for p in ROOT.glob('smali*/**/*.smali'):
        if f'L{c};' in p.read_text(errors='ignore'): hits.append(str(p.relative_to(ROOT)))
    if hits: raise SystemExit(f'{c} dangling refs: {hits[:20]}')
print('Perfetto subsystem physically removed')
