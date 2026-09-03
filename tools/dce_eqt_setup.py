#!/usr/bin/env python3
from pathlib import Path
import re,collections,shutil
P=Path('/mnt/data/meboard_work/buildtree/smali/eqt.smali')
text=P.read_text(); lines=text.splitlines()
SETUP={'<init>','be','bf','bg','bh','bi','bj','bk','bl','bm','bn','bo'}
DCE_METHODS={'be','bf','bg','bh','bi','bj','bk','bl','bm','bn'}

def mname(h):
 m=re.search(r' ([^ (]+)\(',h); return m.group(1) if m else ''
methods=[];i=0
while i<len(lines):
 if lines[i].startswith('.method'):
  st=i;h=lines[i];i+=1
  while i<len(lines) and lines[i] != '.end method':i+=1
  methods.append((st,i,h))
 i+=1
fdeps=collections.defaultdict(set); external=collections.defaultdict(list)
for st,en,h in methods:
 n=mname(h)
 if n not in SETUP:
  for j in range(st,en+1):
   for m in re.finditer(r'iget-object\s+\w+,\s+\w+,\s+Leqt;->([A-Za-z0-9]+):Laals;',lines[j]): external[m.group(1)].append((n,j+1))
  continue
 regs=collections.defaultdict(set); pending=None
 for j in range(st+1,en):
  l=lines[j].strip()
  if not l or l.startswith('.') or l.startswith(':') or l.startswith('#'): continue
  if pending is not None and not l.startswith('move-result'): pending=None
  m=re.match(r'move-object(?:/from16|/16)?\s+(\w+),\s+(\w+)',l)
  if m: regs[m.group(1)]=set(regs[m.group(2)]); continue
  m=re.match(r'move(?:/from16|/16)?\s+(\w+),\s+(\w+)',l)
  if m: regs[m.group(1)]=set(regs[m.group(2)]); continue
  m=re.match(r'(?:sget-object|new-instance)\s+(\w+),',l)
  if m: regs[m.group(1)]=set(); continue
  m=re.match(r'iget-object\s+(\w+),\s+\w+,\s+Leqt;->([A-Za-z0-9]+):Laals;',l)
  if m: regs[m.group(1)]={m.group(2)}; continue
  m=re.match(r'iget-object\s+(\w+),',l)
  if m: regs[m.group(1)]=set(); continue
  m=re.match(r'const(?:/\w+)?\s+(\w+),',l)
  if m: regs[m.group(1)]=set(); continue
  if l.startswith('check-cast '): continue
  m=re.match(r'invoke-(direct|static|virtual|interface|super)(/range)?\s+\{([^}]*)\},\s+L([^;]+);->([^ (]+)',l)
  if m:
   kind,rng,argtxt,cls,meth=m.groups();args=[]
   if rng and '..' in argtxt:
    aa=[x.strip() for x in argtxt.split('..')];ma=re.match(r'([vp])(\d+)',aa[0]);mb=re.match(r'([vp])(\d+)',aa[-1])
    if ma and mb and ma.group(1)==mb.group(1):args=[f'{ma.group(1)}{k}' for k in range(int(ma.group(2)),int(mb.group(2))+1)]
   elif argtxt.strip():args=[x.strip() for x in argtxt.split(',')]
   dep=set().union(*(regs.get(a,set()) for a in args)) if args else set()
   if meth=='<init>' and args: regs[args[0]]=set(dep)
   if kind=='static' and cls=='aall' and meth=='b' and len(args)>=2:
    left=set(regs.get(args[0],set()));right=set().union(*(regs.get(a,set()) for a in args[1:]))
    for f in left:fdeps[f]|=right-{f}
   pending=dep;continue
  m=re.match(r'move-result-object\s+(\w+)',l)
  if m: regs[m.group(1)]=set(pending or ());pending=None;continue
  m=re.match(r'iput-object\s+(\w+),\s+\w+,\s+Leqt;->([A-Za-z0-9]+):Laals;',l)
  if m:
   r,f=m.groups();fdeps[f]|=set(regs.get(r,set()))-{f};continue
live=set(external);q=list(live)
while q:
 f=q.pop()
 for d in fdeps.get(f,()):
  if d not in live:live.add(d);q.append(d)
print('live provider fields',len(live))

def args_of(argtxt,rng):
 if rng and '..' in argtxt:
  aa=[x.strip() for x in argtxt.split('..')];ma=re.match(r'([vp])(\d+)',aa[0]);mb=re.match(r'([vp])(\d+)',aa[-1])
  if ma and mb and ma.group(1)==mb.group(1):return [f'{ma.group(1)}{k}' for k in range(int(ma.group(2)),int(mb.group(2))+1)]
 return [x.strip() for x in argtxt.split(',') if x.strip()]

def dce_body(body,name):
 raw=body.splitlines(); execs=[]
 for idx,l in enumerate(raw):
  s=l.strip()
  if not s or s.startswith('.') or s.startswith(':') or s.startswith('#'):continue
  execs.append((idx,s,l))
 alias=collections.defaultdict(set); delegate_live=set()
 for k,(idx,s,orig) in enumerate(execs):
  m=re.match(r'move(?:-object)?(?:/from16|/16)?\s+(\w+),\s+(\w+)',s)
  if m:alias[m.group(1)]=set(alias[m.group(2)]);continue
  m=re.match(r'iget-object\s+(\w+),\s+\w+,\s+Leqt;->([A-Za-z0-9]+):Laals;',s)
  if m:alias[m.group(1)]={m.group(2)};continue
  m=re.match(r'(?:iget-object|sget-object|new-instance|const(?:/\w+)?)\s+(\w+),',s)
  if m:alias[m.group(1)]=set();continue
  if s.startswith('check-cast '):continue
  m=re.match(r'iput-object\s+(\w+),\s+\w+,\s+Leqt;->([A-Za-z0-9]+):Laals;',s)
  if m:alias[m.group(1)].add(m.group(2));continue
  m=re.match(r'invoke-(direct|static|virtual|interface|super)(/range)?\s+\{([^}]*)\},\s+L([^;]+);->([^ (]+)',s)
  if m:
   kind,rng,at,cls,meth=m.groups();args=args_of(at,rng)
   if kind=='static' and cls=='aall' and meth=='b' and args and (alias.get(args[0],set()) & live):delegate_live.add(k)
   continue
  m=re.match(r'move-result-object\s+(\w+)',s)
  if m:alias[m.group(1)]=set();continue
 result_invoke={}
 for k,(idx,s,orig) in enumerate(execs):
  if s.startswith('move-result') and k>0 and execs[k-1][1].startswith('invoke-'):result_invoke[k]=k-1
 needed=set();keep=set();force_invoke=set()
 for k in range(len(execs)-1,-1,-1):
  idx,s,orig=execs[k]
  if s=='return-void':keep.add(k);continue
  m=re.match(r'iput-object\s+(\w+),\s+\w+,\s+Leqt;->([A-Za-z0-9]+):Laals;',s)
  if m:
   src,f=m.groups()
   if f in live:keep.add(k);needed.add(src)
   continue
  m=re.match(r'move-result-object\s+(\w+)',s)
  if m:
   d=m.group(1)
   if d in needed:
    keep.add(k);needed.discard(d)
    if k in result_invoke:force_invoke.add(result_invoke[k])
   continue
  m=re.match(r'invoke-(direct|static|virtual|interface|super)(/range)?\s+\{([^}]*)\},\s+L([^;]+);->([^ (]+)',s)
  if m:
   kind,rng,at,cls,meth=m.groups();args=args_of(at,rng);essential=False
   if k in force_invoke:essential=True
   elif meth=='<init>' and args and args[0] in needed:essential=True
   elif kind in {'virtual','interface'} and args and args[0] in needed:essential=True
   elif k in delegate_live:essential=True
   if essential:keep.add(k);needed.update(args)
   continue
  m=re.match(r'(move(?:-object)?(?:/from16|/16)?)\s+(\w+),\s+(\w+)',s)
  if m:
   d,src=m.group(2),m.group(3)
   if d in needed:keep.add(k);needed.discard(d);needed.add(src)
   continue
  m=re.match(r'iget-object\s+(\w+),\s+(\w+),\s+Leqt;->([A-Za-z0-9]+):Laals;',s)
  if m:
   d=m.group(1)
   if d in needed:keep.add(k);needed.discard(d)
   continue
  m=re.match(r'(?:iget-object|sget-object|new-instance|const(?:/\w+)?)\s+(\w+),',s)
  if m:
   d=m.group(1)
   if d in needed:keep.add(k);needed.discard(d)
   continue
  m=re.match(r'check-cast\s+(\w+),',s)
  if m:
   if m.group(1) in needed:keep.add(k)
   continue
  raise SystemExit(f'unhandled executable in {name}: {s}')
 unresolved={r for r in needed if r.startswith('v')}
 if unresolved:raise SystemExit(f'{name}: unresolved local regs after DCE: {sorted(unresolved)}')
 locals_line=next((l for l in raw if l.strip().startswith('.locals ')),None)
 if not locals_line:raise SystemExit(f'{name}: no locals')
 out=[locals_line,'']
 for k,(idx,s,orig) in enumerate(execs):
  if k in keep:out.append(orig)
 out.append('')
 print(name,'exec',len(execs),'kept',len(keep),'removed',len(execs)-len(keep))
 return '\n'.join(out)

for st,en,h in reversed(methods):
 n=mname(h)
 if n not in DCE_METHODS:continue
 pat=re.compile(rf'(?ms)^(\.method private final {re.escape(n)}\(\)V\n)(.*?)(^\.end method)')
 m=pat.search(text)
 if not m:raise SystemExit(f'method {n} not found')
 text=text[:m.start(2)]+dce_body(m.group(2),n)+text[m.end(2):]
lines2=text.splitlines(); refs=collections.Counter()
for l in lines2:
 if l.startswith('.field '):continue
 for m in re.finditer(r'Leqt;->([A-Za-z0-9]+):Laals;',l):refs[m.group(1)]+=1
out=[]; removed_fields=[]
for l in lines2:
 m=re.match(r'^\.field ([A-Za-z0-9]+):Laals;$',l)
 if m and refs[m.group(1)]==0:removed_fields.append(m.group(1));continue
 out.append(l)
text='\n'.join(out)+'\n'
for c in ['qji','qjj','qjk','qjl','qjm']:
 if f'L{c};' in text:raise SystemExit(f'{c} still referenced in eqt after DCE')
P.write_text(text)
print('removed unreferenced provider fields',len(removed_fields))
print('qji-qjm provider setup references gone')
