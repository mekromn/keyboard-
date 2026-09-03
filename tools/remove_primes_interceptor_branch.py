#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path('/mnt/data/meboard_work/buildtree')
abil=ROOT/'smali_classes3/abil.smali'
s=abil.read_text()
callers=[]
for p in ROOT.glob('smali*/**/*.smali'):
    t=p.read_text(errors='ignore')
    if 'Labil;-><init>(Ljava/lang/Object;I)V' in t:
        callers.append(p)
s=s.replace('.field private final synthetic b:I\n\n','')
s=s.replace('.method public constructor <init>(Ljava/lang/Object;I)V','.method public constructor <init>(Ljava/lang/Object;)V',1)
s,n=re.subn(r'(?ms)\n\s*\.line 1\n\s*iput p2, p0, Labil;->b:I\n','\n',s,count=1)
if n!=1: raise SystemExit('abil discriminator ctor store missing')
pat=re.compile(r'(?ms)^\.method public final a\(Laasu;Laaps;Laapt;\)Lytg;\n.*?^\.end method',re.M)
m=pat.search(s)
if not m: raise SystemExit('abil.a missing')
method='''.method public final a(Laasu;Laaps;Laapt;)Lytg;
    .locals 1

    new-instance v0, Labik;
    invoke-virtual {p3, p1, p2}, Laapt;->b(Laasu;Laaps;)Lytg;
    move-result-object p1
    invoke-direct {v0, p0, p1}, Labik;-><init>(Labil;Lytg;)V
    return-object v0
.end method'''
s=s[:m.start()]+method+s[m.end():]
abil.write_text(s)
for p in callers:
    t=p.read_text()
    t2,n=re.subn(r'invoke-direct \{([^,}]+),\s*([^,}]+),\s*[^}]+\}, Labil;-><init>\(Ljava/lang/Object;I\)V',r'invoke-direct {\1, \2}, Labil;-><init>(Ljava/lang/Object;)V',t)
    if n: p.write_text(t2)
mdd=ROOT/'smali_classes2/mdd.smali'
refs=[]
for p in ROOT.glob('smali*/**/*.smali'):
    if p==mdd: continue
    if 'Lmdd;' in p.read_text(errors='ignore'): refs.append(str(p))
if refs: raise SystemExit(f'mdd still referenced: {refs}')
mdd.unlink()
ats=abil.read_text()
for needle in ['Lvpu;->iM()', 'Lmdb;', 'Lmdh;', 'Lmdf;', 'SystemClock;->elapsedRealtime', 'https://']:
    if needle in ats: raise SystemExit(f'abil telemetry residue remains: {needle}')
print(f'Simplified abil to non-telemetry interceptor; updated {len(callers)} callers; deleted orphan mdd')
