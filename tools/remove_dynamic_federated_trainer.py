#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path('/mnt/data/meboard_work/buildtree')

def find(cls):
    hits=list(ROOT.glob(f'smali*/**/{cls}.smali'))
    if len(hits)!=1: raise SystemExit(f'{cls}: expected one file, got {hits}')
    return hits[0]

def method_ranges(text):
    out=[];pos=0
    while True:
        m=re.search(r'^\.method[^\n]*\n',text[pos:],re.M)
        if not m: break
        a=pos+m.start(); b=text.find('\n.end method',pos+m.end())
        if b<0: raise SystemExit('unterminated method')
        b += len('\n.end method');out.append((a,b,text[a:b]));pos=b
    return out

def prune_packed(body, case):
    changed=0
    for dm in list(re.finditer(r'(?ms)(^\s*:pswitch_data_[0-9a-f]+\s*\n\s*\.packed-switch\s+0x([0-9a-f]+)\s*\n)(.*?)(^\s*\.end packed-switch)',body,re.M))[::-1]:
        base=int(dm.group(2),16);labels=re.findall(r':pswitch_[0-9a-f]+',dm.group(3));cmap={base+i:l for i,l in enumerate(labels)}
        if case not in cmap: continue
        lab=cmap[case]; data_pos=dm.start();ms=list(re.finditer(rf'(?m)^\s*{re.escape(lab)}\s*$',body[:data_pos]))
        if not ms: continue
        st=ms[-1].start(); nxt=re.search(r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',body[ms[-1].end():data_pos]); en=ms[-1].end()+nxt.start() if nxt else data_pos
        if 'Lrih;' not in body[st:en]: continue
        keep=[c for c in cmap if c!=case]; repl=cmap[min(keep,key=lambda c:abs(c-case))]
        data=dm.group(3);data,n=re.subn(rf'(?m)^(\s*){re.escape(lab)}\s*$',rf'\1{repl}',data,count=1)
        if n!=1: raise SystemExit(f'failed switch table rewrite {case}')
        body=body[:dm.start(3)]+data+body[dm.end(3):]
        data_pos=body.rfind(dm.group(1).splitlines()[0].strip());ms=list(re.finditer(rf'(?m)^\s*{re.escape(lab)}\s*$',body[:data_pos]));st=ms[-1].start();nxt=re.search(r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',body[ms[-1].end():data_pos]);en=ms[-1].end()+nxt.start() if nxt else data_pos
        seg=body[st:en];outside=body[:st]+body[en:data_pos];preserve=en
        for lm in re.finditer(r'(?m)^\s*(:[A-Za-z0-9_]+)\s*$',seg):
            l2=lm.group(1)
            if l2.startswith(':pswitch_'): continue
            if re.search(rf'(?<![A-Za-z0-9_]){re.escape(l2)}(?![A-Za-z0-9_])',outside): preserve=min(preserve,st+lm.start())
        body=body[:st]+body[preserve:];changed+=1
    return body,changed

def prune_class(cls, case, expected):
    p=find(cls);t=p.read_text();count=0
    for a,b,body in reversed(method_ranges(t)):
        if 'Lrih;' not in body or 'packed-switch' not in body: continue
        nb,n=prune_packed(body,case)
        if n:t=t[:a]+nb+t[b:];count+=n
    if count!=expected: raise SystemExit(f'{cls}: expected {expected} DynamicTrainer branch removals, got {count}')
    p.write_text(t);print(cls,'removed dynamic trainer case',case,'x',count)

p=find('eqt');lines=p.read_text().splitlines();mi=next(i for i,l in enumerate(lines) if l.startswith('.method public final aI()Ljava/util/Set;'));me=next(i for i in range(mi+1,len(lines)) if lines[i]=='.end method');m=lines[mi:me+1]
arr=next(i for i,l in enumerate(m) if 'new-array v11, v11, [Lpth;' in l);start=next(i for i in range(arr+1,len(m)) if re.match(r'\s*new-instance\s+v4,\s+Lrii;',m[i]));end=next(i for i in range(start,len(m)) if re.match(r'\s*aput-object\s+v4,\s+v11,\s+v23',m[i]));del m[start:end+1]
out=[];idx=0
for line in m:
    if re.match(r'\s*aput-object\s+\w+,\s+v11,\s+v23\s*$',line):
        while out and re.match(r'\s*const/16\s+v23,\s+0x[0-9a-f]+\s*$',out[-1]): out.pop()
        out.append(f'    const/16 v23, 0x{idx:x}');out.append(line);idx+=1
    else:out.append(line)
m=out;arr=next(i for i,l in enumerate(m) if 'new-array v11, v11, [Lpth;' in l)
for j in range(arr-1,max(-1,arr-14),-1):
    if re.match(r'\s*const/16\s+v11,\s+0x[0-9a-f]+\s*$',m[j]):m[j]=f'    const/16 v11, 0x{idx:x}';break
else:raise SystemExit('registry size const missing')
lines[mi:me+1]=m;p.write_text('\n'.join(lines)+'\n');print('eqt registry now',idx,'modules')
p=find('frp');t=p.read_text();pat=re.compile(r'(?ms)^\.method public constructor <init>\(Lrih;I\)V\n.*?^\.end method\n?');t,n=pat.subn('',t,count=1)
if n!=1:raise SystemExit('frp typed DynamicTrainer constructor missing')
p.write_text(t)
prune_class('frp',7,2);prune_class('foo',12,1);prune_class('fvx',12,1);prune_class('rig',0,1);prune_class('rif',0,1);prune_class('iwg',10,1);prune_class('osn',13,1)
classes={}
for f in ROOT.glob('smali*/**/*.smali'):
    tx=f.read_text(errors='ignore');mm=re.search(r'^\.class[^\n]* L([^;]+);',tx,re.M)
    if mm:classes[mm.group(1)]=(f,tx)
D={'rii','rih','rij'}
for c in D:
    ext=[x for x,(_,tx) in classes.items() if x not in D and f'L{c};' in tx]
    if ext:raise SystemExit(f'{c}: external refs remain {ext[:30]}')
for c in D:classes[c][0].unlink();print('deleted',c)
print('DynamicTrainer federated module physically removed; LocalComputationTaskManager/Brella local wrapper retained')
