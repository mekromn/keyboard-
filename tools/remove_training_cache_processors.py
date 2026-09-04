#!/usr/bin/env python3
"""Physically remove Java-side training-cache metrics/export processors."""
from pathlib import Path
import re
import subprocess

ROOT = Path('/mnt/data/meboard_work/buildtree')
SMALI_ROOTS = [ROOT / name for name in ('smali','smali_classes2','smali_classes3','smali_classes4')]
DELETE = {'gug','guh','gui','guj','jyq','jyr','jys','jyv','jyw','rhc'}
CASE_REMOVALS = {
    'guf': {0, 2},
    'gab': {12},
    'frm': {18},
    'fte': {6},
    'gaj': {14, 15, 16},
    'jlw': {7},
    'iee': {3},
}
EXPECTED_INBOUND = {
    'gug': {'guf','guh','gui'}, 'guh': {'gug'}, 'gui': set(), 'guj': {'gui'},
    'jyq': {'jyr','jys'}, 'jyr': {'jyq'}, 'jys': {'iee'},
    'jyv': {'gaj','jlw','jys','jyw'}, 'jyw': {'jyv'}, 'rhc': {'guj','jys'},
}
EXPECTED_CONSTRUCTOR_SITES = {
    ('guf',0): {'guh':1}, ('guf',2): {'guh':1}, ('gab',12): {'guh':1},
    ('frm',18): {'guh':1}, ('fte',6): {'jyw':1}, ('gaj',14): {'jyw':1},
    ('gaj',15): {'jyw':1}, ('gaj',16): {'jyw':2}, ('jlw',7): {'jyw':1},
    ('iee',3): {'jys':1},
}
MARKERS = {
    'gug':'ExpressionTrainingDataMetricsProcessor',
    'guh':'ExpressionTrainingDataMetricsProcessorHelper',
    'gui':'ExpressionTrainingDataProcessorProviderModule',
    'jyq':'InputViewSessionMetricsProcessor',
    'jyr':'InputViewSessionMetricsProcessorHelper',
    'jys':'NebulaeProcessorProvider$ProviderModule',
    'jyv':'NebulaeTrainingCacheMetricsProcessor',
    'jyw':'NebulaeTrainingCacheMetricsProcessorHelper',
}


def find_class(name):
    hits=[]
    for root in SMALI_ROOTS:
        hits.extend(root.rglob(name+'.smali'))
    if len(hits)!=1:
        raise SystemExit(f'{name}: expected one class file, got {hits}')
    return hits[0]


def declared_name(path):
    m=re.search(r'^\.class[^\n]* L([^;]+);',path.read_text(errors='ignore'),re.M)
    if not m: raise SystemExit(f'{path}: missing class declaration')
    return m.group(1)


def rg_files(needle):
    cmd=['rg','-l','-F',needle,*map(str,SMALI_ROOTS),'--glob','*.smali']
    run=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if run.returncode not in (0,1):
        raise SystemExit(run.stderr)
    return [Path(x) for x in run.stdout.splitlines()]


def inbound(name):
    own=find_class(name)
    return {declared_name(p) for p in rg_files(f'L{name};') if p!=own}


def constructor_sites(target,wanted):
    result={}
    call_re=re.compile(rf'invoke-direct(?:/range)?\s+\{{([^}}]*)\}},\s+L{target};-><init>\(([^)]*)\)V')
    for path in rg_files(f'L{target};-><init>'):
        regs={}
        for line in path.read_text(errors='ignore').splitlines():
            s=line.strip()
            if s.startswith('.method'):
                regs={}; continue
            m=re.match(r'const(?:/4|/16|/high16)?\s+(\w+),\s+(-?0x[0-9a-f]+|-?\d+)',s)
            if m:
                try: regs[m.group(1)]=int(m.group(2),0)
                except ValueError: pass
                continue
            m=re.match(r'move(?:-object)?(?:/from16|/16)?\s+(\w+),\s+(\w+)',s)
            if m:
                regs[m.group(1)]=regs.get(m.group(2)); continue
            m=call_re.search(s)
            if m:
                args=[x.strip() for x in m.group(1).split(',') if x.strip()]
                if args and regs.get(args[-1])==wanted:
                    owner=declared_name(path); result[owner]=result.get(owner,0)+1
    return result


def method_ranges(text):
    out=[]; pos=0
    while True:
        m=re.search(r'^\.method[^\n]*\n',text[pos:],re.M)
        if not m: break
        a=pos+m.start(); b=text.find('\n.end method',pos+m.end())
        if b<0: raise SystemExit('unterminated method')
        b+=len('\n.end method'); out.append((a,b,text[a:b])); pos=b
    return out


def prune_cases(path,removed):
    text=path.read_text(); methods_changed=branches_removed=tables_seen=0
    for ma,mb,body in reversed(method_ranges(text)):
        changed=0
        data_matches=list(re.finditer(
            r'(?ms)^\s*(:pswitch_data_[0-9a-f]+)\s*\n'
            r'\s*\.packed-switch\s+(-?0x[0-9a-f]+|-?\d+)\s*\n'
            r'(.*?)^\s*\.end packed-switch',body,re.M))
        for dm in reversed(data_matches):
            base=int(dm.group(2),0); labels=re.findall(r':pswitch_[0-9a-f]+',dm.group(3))
            cmap={base+i:l for i,l in enumerate(labels)}; active=removed & set(cmap)
            if not active: continue
            tables_seen+=1; retained=[c for c in cmap if c not in active]
            if not retained: raise SystemExit(f'{path.name}: all cases selected')
            data=dm.group(3)
            for case in sorted(active):
                old=cmap[case]; repl=cmap[min(retained,key=lambda c:abs(c-case))]
                data,n=re.subn(rf'(?m)^(\s*){re.escape(old)}\s*$',rf'\1{repl}',data,count=1)
                if n!=1: raise SystemExit(f'{path.name}: table case {case} count {n}')
            body=body[:dm.start(3)]+data+body[dm.end(3):]
            table_pos=body.rfind(dm.group(1)); removals=[]
            for case in sorted(active):
                lab=cmap[case]; ms=list(re.finditer(rf'(?m)^\s*{re.escape(lab)}\s*$',body[:table_pos]))
                if not ms: raise SystemExit(f'{path.name}: code label missing case {case}')
                st=ms[-1].start(); nxt=re.search(r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',body[ms[-1].end():table_pos])
                en=ms[-1].end()+nxt.start() if nxt else table_pos
                seg=body[st:en]; outside=body[:st]+body[en:table_pos]; preserve=en
                for lm in re.finditer(r'(?m)^\s*(:[A-Za-z0-9_]+)\s*$',seg):
                    l2=lm.group(1)
                    if l2.startswith(':pswitch_'): continue
                    if re.search(rf'(?<![A-Za-z0-9_]){re.escape(l2)}(?![A-Za-z0-9_])',outside):
                        preserve=min(preserve,st+lm.start())
                if preserve<=st: raise SystemExit(f'{path.name}: empty removal case {case}')
                removals.append((st,preserve))
            for st,en in sorted(removals,reverse=True):
                body=body[:st]+body[en:]; branches_removed+=1; changed+=1
        if changed:
            text=text[:ma]+body+text[mb:]; methods_changed+=1
    if not tables_seen or not branches_removed:
        raise SystemExit(f'{path.name}: target cases not found')
    path.write_text(text)
    print(f'{path.name}: removed {branches_removed} branches across {methods_changed} methods')

paths={name:find_class(name) for name in DELETE | set(CASE_REMOVALS)}
for name,marker in MARKERS.items():
    if marker not in paths[name].read_text(errors='ignore'):
        raise SystemExit(f'{name}: missing marker {marker}')
for name,expected in EXPECTED_INBOUND.items():
    actual=inbound(name)
    if actual!=expected: raise SystemExit(f'{name}: inbound {sorted(actual)} != {sorted(expected)}')
for key,expected in EXPECTED_CONSTRUCTOR_SITES.items():
    actual=constructor_sites(*key)
    if actual!=expected: raise SystemExit(f'{key}: sites {actual} != {expected}')

for name,cases in CASE_REMOVALS.items(): prune_cases(paths[name],cases)
bytes_removed=sum(paths[name].stat().st_size for name in DELETE)
for name in sorted(DELETE): paths[name].unlink(); print('deleted',name)
for name in DELETE:
    hits=rg_files(f'L{name};')
    if hits: raise SystemExit(f'{name}: residual refs {[str(p.relative_to(ROOT)) for p in hits[:20]]}')
for marker in MARKERS.values():
    hits=rg_files(marker)
    if hits: raise SystemExit(f'{marker}: residual {[str(p.relative_to(ROOT)) for p in hits[:20]]}')
print(f'physically removed Java training-cache exporters: {len(DELETE)} classes / {bytes_removed} smali bytes')
