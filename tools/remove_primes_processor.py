#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path('/mnt/data/meboard_work/buildtree')
eq=ROOT/'smali/eqt.smali'; s=eq.read_text()
for sig in [r'aX\(\)V',r'ay\(\)Ltvv;',r'az\(\)Lubr;']:
    pat=re.compile(rf'(?ms)^\.method public final {sig}\n.*?^\.end method\n?')
    s,n=pat.subn('',s,count=1)
    if n!=1: raise SystemExit(f'missing eqt {sig}')
s,n=re.subn(r'(?m)^\.implements Lqjf;\n','',s,count=1)
if n!=1: raise SystemExit('eqt qjf interface missing')
eq.write_text(s)
for c in ['qjf','qjn','qjo']:
    hits=list(ROOT.glob(f'smali*/**/{c}.smali'))
    if len(hits)!=1: raise SystemExit((c,hits))
    hits[0].unlink(); print('deleted',c)
for c in ['qjf','qjn','qjo']:
    refs=[]
    for p in ROOT.glob('smali*/**/*.smali'):
        if f'L{c};' in p.read_text(errors='ignore'): refs.append(str(p.relative_to(ROOT)))
    if refs: raise SystemExit(f'{c} dangling {refs[:20]}')
print('Primes component interface + metrics processor/helper removed')
