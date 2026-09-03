#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path('/mnt/data/meboard_work/buildtree')
p=ROOT/'smali/plf.smali'
text=p.read_text()
REMOVE={7,9,10}

def methods(text):
    out=[]; pos=0
    while True:
        m=re.search(r'^\.method[^\n]*\n',text[pos:],re.M)
        if not m: break
        a=pos+m.start(); b=text.find('\n.end method',pos+m.end())
        if b<0: raise SystemExit('unterminated method')
        b+=len('\n.end method')
        out.append((a,b,text[a:b])); pos=b
    return out

def prune(body):
    dm=re.search(r'(?ms)^\s*:pswitch_data_0\s*\n\s*\.packed-switch\s+0x([0-9a-f]+)\s*\n(.*?)^\s*\.end packed-switch',body,re.M)
    if not dm: return body,0
    base=int(dm.group(1),16); labs=re.findall(r':pswitch_[0-9a-f]+',dm.group(2))
    cmap={base+i:l for i,l in enumerate(labs)}
    rem={c for c in REMOVE if c in cmap}
    if not rem: return body,0
    keep=[c for c in cmap if c not in rem]; repl=cmap[keep[0]]
    data=dm.group(2)
    for c in rem:
        data=re.sub(rf'(?m)^(\s*){re.escape(cmap[c])}\s*$',rf'\1{repl}',data,count=1)
    body=body[:dm.start(2)]+data+body[dm.end(2):]
    data_pos=dm.start(); ranges=[]
    for c in rem:
        lab=cmap[c]
        ms=list(re.finditer(rf'(?m)^\s*{re.escape(lab)}\s*$',body[:data_pos]))
        if not ms: continue
        st=ms[-1].start()
        nxt=re.search(r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',body[ms[-1].end():data_pos])
        en=ms[-1].end()+nxt.start() if nxt else data_pos
        seg=body[st:en]; preserve=en
        for lm in re.finditer(r'(?m)^\s*(:[A-Za-z0-9_]+)\s*$',seg):
            lab2=lm.group(1)
            if lab2.startswith(':pswitch_'): continue
            abspos=st+lm.start(); outside=body[:st]+body[en:data_pos]
            if re.search(rf'(?<![A-Za-z0-9_]){re.escape(lab2)}(?![A-Za-z0-9_])',outside):
                preserve=min(preserve,abspos)
        ranges.append((st,preserve))
    for st,en in sorted(ranges,reverse=True): body=body[:st]+body[en:]
    return body,len(ranges)

changed=0
for a,b,body in reversed(methods(text)):
    if 'packed-switch' not in body: continue
    nb,n=prune(body)
    if n: text=text[:a]+nb+text[b:]; changed+=n
for typ in ['Lrer;','Lrgj;','Lrgk;']:
    pat=re.compile(rf'(?ms)^\.method public constructor <init>\({re.escape(typ)}I\)V\n.*?^\.end method\n?')
    text,n=pat.subn('',text,count=1)
    if n!=1: raise SystemExit(f'constructor {typ} not found')
p.write_text(text)
print('pruned plf branch bodies',changed)
for c in ['rer','res','rgj','rgk']:
    hits=list(ROOT.glob(f'smali*/**/{c}.smali'))
    if len(hits)!=1: raise SystemExit((c,hits))
    hits[0].unlink(); print('deleted',c)
for c in ['rer','res','rgj','rgk']:
    refs=[]
    for f in ROOT.glob('smali*/**/*.smali'):
        if f'L{c};' in f.read_text(errors='ignore'): refs.append(str(f.relative_to(ROOT)))
    if refs: raise SystemExit(f'{c} dangling {refs[:20]}')
print('training cache guarder + maintainer physically removed')
