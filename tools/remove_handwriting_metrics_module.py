#!/usr/bin/env python3
"""Remove HandwritingMetrics module without removing handwriting input."""
from pathlib import Path
import re

ROOT=Path('/mnt/data/meboard_work/buildtree')
EQT=ROOT/'smali/eqt.smali'


def find(cls):
    hits=list(ROOT.glob(f'smali*/**/{cls}.smali'))
    if len(hits)!=1: raise SystemExit(f'{cls}: expected one file, got {hits}')
    return hits[0]


def remove_registry_factory(text, dispatcher, disc):
    mm=re.search(r'(?ms)^\.method public final aI\(\)Ljava/util/Set;\n.*?^\.end method',text,re.M)
    if not mm: raise SystemExit('eqt.aI missing')
    lines=mm.group(0).splitlines(); arr=next(i for i,l in enumerate(lines) if 'new-array v11, v11, [Lpth;' in l)
    regs={}; target=None; pending=None
    for i,l in enumerate(lines):
        s=l.strip()
        m=re.match(r'const(?:/4|/16)?\s+(v\d+),\s+(-?0x[0-9a-f]+|-?\d+)',s)
        if m: regs[m.group(1)]=int(m.group(2),0)
        m=re.match(r'move(?:/from16|/16)?\s+(v\d+),\s+(v\d+)',s)
        if m: regs[m.group(1)]=regs.get(m.group(2))
        m=re.match(r'invoke-direct \{(v\d+),\s*(v\d+)\}, L([^;]+);-><init>\(I\)V',s)
        if m and m.group(3)==dispatcher and regs.get(m.group(2))==disc:
            obj=m.group(1); start=next((j for j in range(i,-1,-1) if re.match(rf'\s*new-instance\s+{obj},\s+L{dispatcher};',lines[j])),None)
            if start is None: raise SystemExit('factory allocation missing')
            pending=(start,obj)
        if pending and re.match(rf'\s*aput-object\s+{pending[1]},\s+v11,\s+v23\s*$',l):
            if target is not None: raise SystemExit('duplicate target factory')
            target=(pending[0],i);pending=None
    if target is None: raise SystemExit(f'{dispatcher} discriminator {disc} registry factory missing')
    del lines[target[0]:target[1]+1]
    arr=next(i for i,l in enumerate(lines) if 'new-array v11, v11, [Lpth;' in l)
    stores=[i for i in range(arr+1,len(lines)) if re.match(r'\s*aput-object\s+\w+,\s+v11,\s+v23\s*$',lines[i])]
    offset=0
    for idx,pos0 in enumerate(stores):
        pos=pos0+offset
        if pos>0 and re.match(r'\s*const/16\s+v23,\s+0x[0-9a-f]+\s*$',lines[pos-1]):
            del lines[pos-1];pos-=1;offset-=1
        lines.insert(pos,f'    const/16 v23, 0x{idx:x}');offset+=1
    arr=next(i for i,l in enumerate(lines) if 'new-array v11, v11, [Lpth;' in l)
    for j in range(arr-1,max(-1,arr-16),-1):
        if re.match(r'\s*const/16\s+v11,\s+0x[0-9a-f]+\s*$',lines[j]):
            lines[j]=f'    const/16 v11, 0x{len(stores):x}';break
    else: raise SystemExit('module count constant missing')
    print(f'eqt.aI: removed {dispatcher} discriminator {disc}; registry now {len(stores)}')
    return text[:mm.start()]+'\n'.join(lines)+text[mm.end():]


def strip_default_target(dispatcher, target):
    p=find(dispatcher);text=p.read_text();changed=0
    methods=[];pos=0
    while True:
        m=re.search(r'^\.method[^\n]*\n',text[pos:],re.M)
        if not m:break
        a=pos+m.start();b=text.find('\n.end method',pos+m.end())
        if b<0:raise SystemExit('unterminated method')
        b+=len('\n.end method');methods.append((a,b,text[a:b]));pos=b
    for a,b,body in reversed(methods):
        if f'L{target};' not in body or 'packed-switch' not in body:continue
        sw=re.search(r'(?m)^\s*packed-switch\s+\w+,\s+(:pswitch_data_[0-9a-f]+)\s*$',body)
        if not sw:raise SystemExit(f'{dispatcher}: switch not found')
        first=re.search(r'(?m)^\s*(:pswitch_[0-9a-f]+)\s*$',body[sw.end():])
        if not first:raise SystemExit(f'{dispatcher}: first case label missing')
        end=sw.end()+first.start(); label=first.group(1)
        removed=body[sw.end():end]
        if f'L{target};' not in removed:raise SystemExit(f'{dispatcher}: target not confined to default branch')
        body=body[:sw.end()]+f'\n\n    goto {label}\n\n'+body[end:]
        text=text[:a]+body+text[b:];changed+=1
    if changed!=2:raise SystemExit(f'{dispatcher}: expected 2 default branches, removed {changed}')
    if f'L{target};' in text:raise SystemExit(f'{dispatcher}: target reference remains')
    p.write_text(text);print(f'{dispatcher}: physically removed default {target} create/definition branches')

text=EQT.read_text();text=remove_registry_factory(text,'fuz',20)
text,n=re.subn(r'(?m)^\.implements Lgyt;\n','',text,count=1)
if n!=1:raise SystemExit('eqt implements gyt missing')
text,n=re.subn(r'(?ms)^\.method public final s\(\)Lgys;\n.*?^\.end method\n?','',text,count=1)
if n!=1:raise SystemExit('eqt s()Lgys missing')
EQT.write_text(text)
strip_default_target('fuz','gys')

# Remove the metrics-only overload from shared utility wya.
p=find('wya');s=p.read_text();s,n=re.subn(r'(?ms)^\.method public constructor <init>\(Lgyp;Llcw;\)V\n.*?^\.end method\n?','',s,count=1)
if n!=1:raise SystemExit('wya handwriting metrics constructor missing')
p.write_text(s);print('wya: removed metrics-only gyp constructor')

D={'gys','gyp','gyq','gyo','gyt'}
classes={}
for p in ROOT.glob('smali*/**/*.smali'):
    t=p.read_text(errors='ignore');m=re.search(r'^\.class[^\n]* L([^;]+);',t,re.M)
    if m:classes[m.group(1)]=(p,t)
for c in D:
    if c not in classes:raise SystemExit(f'{c} missing')
    ext=[x for x,(_,t) in classes.items() if x not in D and f'L{c};' in t]
    if ext:raise SystemExit(f'{c}: external refs remain {ext[:30]}')
for c in sorted(D):classes[c][0].unlink();print('deleted',c)

# Handwriting event enums and IME implementation remain; only metrics classes are gone.
for keep in ['gyr','gyu','com/google/android/apps/inputmethod/libs/handwriting/ime/HandwritingIme']:
    if keep not in classes:raise SystemExit(f'required handwriting feature class missing: {keep}')
print('HandwritingMetrics module physically removed; handwriting IME retained')
