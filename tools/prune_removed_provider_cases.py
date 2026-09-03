#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path('/mnt/data/meboard_work/buildtree')
CASES={
 'jnv':{1,4,8,14,16,17},
 'evg':{0,9},
 'fuz':{11,14},
 'ogx':{4},
 'qtc':{0,2,7,8,9,10,11,12,13,16,19},
 'pks':{2,5},
 'mus':{4,12},
 'hyy':{0,7,8,9},
 'hal':{4,9,12,14},
 'kbk':{0,5},
 'jyt':{0},
 'ips':{6},
}

def find_file(cls):
    hits=list(ROOT.glob(f'smali*/{cls}.smali'))
    if len(hits)!=1: raise SystemExit(f'{cls}: expected one file, got {hits}')
    return hits[0]

def methods(text):
    out=[]; pos=0
    while True:
        m=re.search(r'^\.method[^\n]*\n',text[pos:],re.M)
        if not m: break
        a=pos+m.start(); hdr=m.group(0).strip(); b=text.find('\n.end method',pos+m.end())
        if b<0: raise ValueError('unterminated method')
        b+=len('\n.end method')
        out.append((a,b,hdr,text[a:b])); pos=b
    return out

def prune_method(body, removed):
    dm=re.search(r'(?m)^(\s*):pswitch_data_0\s*\n\s*\.packed-switch\s+0x([0-9a-f]+)\s*\n(.*?)^\s*\.end packed-switch',body,re.S|re.M)
    if not dm: return body,0
    base=int(dm.group(2),16)
    labels=re.findall(r':pswitch_[0-9a-f]+',dm.group(3))
    if not labels: return body,0
    case_labels={base+i:l for i,l in enumerate(labels)}
    active_removed={c for c in removed if c in case_labels}
    if not active_removed: return body,0
    keep=[c for c in case_labels if c not in active_removed]
    if not keep: raise ValueError('cannot remove every switch case')
    repl_label=case_labels[keep[0]]
    data=dm.group(3)
    for c in active_removed:
        old=case_labels[c]
        data=re.sub(rf'(?m)^(\s*){re.escape(old)}\s*$',rf'\1{repl_label}',data,count=1)
    body=body[:dm.start(3)]+data+body[dm.end(3):]
    data_pos=dm.start()
    removals=[]
    for c in active_removed:
        lab=case_labels[c]
        ms=list(re.finditer(rf'(?m)^\s*{re.escape(lab)}\s*$',body[:data_pos]))
        if not ms: continue
        st=ms[-1].start()
        nxt=re.search(r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',body[ms[-1].end():data_pos])
        en=ms[-1].end()+nxt.start() if nxt else data_pos
        seg=body[st:en]
        preserve=en
        for lm in re.finditer(r'(?m)^\s*(:[A-Za-z0-9_]+)\s*$',seg):
            lab2=lm.group(1)
            if lab2.startswith(':pswitch_'): continue
            abspos=st+lm.start()
            outside=body[:st]+body[en:data_pos]
            if re.search(rf'(?<![A-Za-z0-9_]){re.escape(lab2)}(?![A-Za-z0-9_])',outside):
                preserve=min(preserve,abspos)
        removals.append((st,preserve))
    for st,en in sorted(removals,reverse=True): body=body[:st]+body[en:]
    return body,len(removals)

for cls,removed in CASES.items():
    p=find_file(cls); text=p.read_text(); changed=0
    for a,b,hdr,body in reversed(methods(text)):
        if 'packed-switch' not in body: continue
        nb,n=prune_method(body,removed)
        if n:
            text=text[:a]+nb+text[b:]; changed+=n
    p.write_text(text)
    print(cls,'removed switch branches',changed,'for cases',sorted(removed))
