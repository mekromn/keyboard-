#!/usr/bin/env python3
"""Physically remove all Mozc/Japanese metrics observers and event producers.

The pass is source-marker and graph driven for the exact Gboard 18.0.3 build. It
removes the application module entry, generated provider interfaces, Clearcut
processor, timing processor, listener/event helpers, their synthetic switch
cases, and orphan emission code. Japanese conversion, candidates, dictionaries,
transliteration, and local learning are protected by strict residual/build gates.
"""
from __future__ import annotations
from pathlib import Path
import re
from collections import defaultdict
ROOT=Path('/mnt/data/meboard_work/buildtree')
CLASS_RE=re.compile(r'^\.class[^\n]* L([^;]+);',re.M)
SOURCE_RE=re.compile(r'^\.source\s+"([^"]+)"',re.M)
REF_RE=re.compile(r'L([A-Za-z0-9_$/]+);')
METHOD_RE=re.compile(r'(?ms)^\.method[^\n]*\n.*?^\.end method\n?')
REG_RE=re.compile(r'\b[vp]\d+\b')

def load():
 files={};texts={}
 for p in ROOT.glob('smali*/**/*.smali'):
  t=p.read_text(errors='ignore');m=CLASS_RE.search(t)
  if m:files[m.group(1)]=p;texts[m.group(1)]=t
 return files,texts
files,texts=load()
initial=set()
rx=re.compile(r'(?i)(mozc.*(?:metric|timing)|japanese.*(?:metric|timing)|visual.?metric|metric.?notification|(?:metric|timing).*(?:mozc|japanese))')
for c,t in texts.items():
 src=(SOURCE_RE.search(t).group(1) if SOURCE_RE.search(t) else '')
 path=str(files[c]).lower();evidence=src+'\n'+'\n'.join(x for x in t.splitlines() if rx.search(x))
 if rx.search(evidence) and ('mozc' in evidence.lower() or 'japanese' in evidence.lower() or 'japanese' in path):initial.add(c)
if not (2<=len(initial)<=20):raise SystemExit(f'unexpected initial Mozc metric classes {len(initial)}: {sorted(initial)}')
seed=set(initial)
changed=True
while changed:
 changed=False
 for c,t in texts.items():
  if c in seed:continue
  refs={r for r in REF_RE.findall(t) if r in texts and r!=c}
  if not (refs&seed):continue
  src=(SOURCE_RE.search(t).group(1) if SOURCE_RE.search(t) else '')
  small=len(t)<35000
  generated=bool(re.search(r'(?i)(provider|factory|module|component|listener|event|timing|metric)',src))
  abstract_only=('.method public abstract' in t and 'invoke-' not in t)
  nonseed=refs-seed
  if small and (generated or abstract_only) and len(nonseed)<=2:
   seed.add(c);changed=True
if len(seed)>40:raise SystemExit(f'Mozc metric closure too broad: {len(seed)}')

def methods(t):return [(m.start(),m.end(),m.group(0)) for m in METHOD_RE.finditer(t)]
def switch_cases(body):
 out=[]
 for dm in re.finditer(r'(?ms)(^\s*:pswitch_data_[0-9a-f]+\s*\n\s*\.packed-switch\s+0x([0-9a-f]+)\s*\n)(.*?)(^\s*\.end packed-switch)',body,re.M):
  base=int(dm.group(2),16);labels=re.findall(r':pswitch_[0-9a-f]+',dm.group(3));data_pos=dm.start()
  for i,lab in enumerate(labels):
   ms=list(re.finditer(rf'(?m)^\s*{re.escape(lab)}\s*$',body[:data_pos]))
   if not ms:continue
   st=ms[-1].start();nxt=re.search(r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',body[ms[-1].end():data_pos]);en=ms[-1].end()+nxt.start() if nxt else data_pos
   out.append((dm,base+i,lab,st,en,body[st:en]))
 return out
factory_cases=defaultdict(set)
for c,t in texts.items():
 for _,_,b in methods(t):
  for dm,case,lab,st,en,seg in switch_cases(b):
   if any(f'L{x};' in seg for x in seed):factory_cases[c].add(case)
eq='eqt';p=files[eq];t=p.read_text();mr=next((x for x in methods(t) if x[2].startswith('.method public final aI()Ljava/util/Set;')),None)
if not mr:raise SystemExit('eqt aI registry missing')
a,b,body=mr;lines=body.splitlines();arr=next(i for i,l in enumerate(lines) if re.search(r'new-array\s+v11,\s+v11,\s+\[Lpth;',l));aputs=[i for i in range(arr+1,len(lines)) if re.match(r'\s*aput-object\s+\w+,\s+v11,\s+\w+',lines[i])]
blocks=[];prev=arr
for slot,end in enumerate(aputs):
 start=next((i for i in range(prev+1,end+1) if re.match(r'\s*new-instance\s+',lines[i])),None)
 if start is None:raise SystemExit(f'registry block {slot} start')
 blocks.append((slot,start,end));prev=end
remove_slots=[]
for slot,st,en in blocks:
 bl=lines[st:en+1];regs={};match=False
 for line in bl:
  s=line.strip();m=re.match(r'const(?:/4|/16)?\s+(v\d+),\s+(-?0x[0-9a-f]+|-?\d+)',s)
  if m:regs[m.group(1)]=int(m.group(2),0);continue
  m=re.match(r'move(?:/from16|/16)?\s+(v\d+),\s+(v\d+)',s)
  if m:regs[m.group(1)]=regs.get(m.group(2));continue
  m=re.search(r'invoke-direct\s+\{[^,}]+,\s*(v\d+)\},\s+L([^;]+);-><init>\(I\)V',s)
  if m and m.group(2) in factory_cases and regs.get(m.group(1)) in factory_cases[m.group(2)]:match=True
  if any(f'L{x};' in s for x in seed):match=True
 if match:remove_slots.append(slot)
if not remove_slots:raise SystemExit(f'no Mozc metric registry slot found; factories={dict(factory_cases)}')
for slot,st,en in reversed(blocks):
 if slot in remove_slots:del lines[st:en+1]
out=[];idx=0
for line in lines:
 if re.match(r'\s*aput-object\s+\w+,\s+v11,\s+\w+\s*$',line):
  while out and re.match(r'\s*const/16\s+v23,\s+0x[0-9a-f]+\s*$',out[-1]):out.pop()
  obj=re.match(r'(\s*)aput-object\s+(\w+),\s+v11,\s+\w+',line)
  out.append(f'{obj.group(1)}const/16 v23, 0x{idx:x}');out.append(f'{obj.group(1)}aput-object {obj.group(2)}, v11, v23');idx+=1
 else:out.append(line)
lines=out;arr=next(i for i,l in enumerate(lines) if 'new-array v11, v11, [Lpth;' in l)
for j in range(arr-1,max(-1,arr-15),-1):
 if re.match(r'\s*const/16\s+v11,\s+0x[0-9a-f]+\s*$',lines[j]):lines[j]=f'    const/16 v11, 0x{idx:x}';break
else:raise SystemExit('registry length constant missing')
nb='\n'.join(lines)+('\n' if body.endswith('\n') else '');t=t[:a]+nb+t[b:];p.write_text(t)
print('removed registry slots',remove_slots,'remaining',idx)

def prune_one(body,case,lab,dm,st,en):
 labels=re.findall(r':pswitch_[0-9a-f]+',dm.group(3));base=int(dm.group(2),16);cmap={base+i:x for i,x in enumerate(labels)};keep=[c for c in cmap if c!=case]
 repl=cmap[min(keep,key=lambda x:abs(x-case))];data=dm.group(3);data,n=re.subn(rf'(?m)^(\s*){re.escape(lab)}\s*$',rf'\1{repl}',data,count=1)
 if n!=1:raise SystemExit(f'switch rewrite case {case}')
 body=body[:dm.start(3)]+data+body[dm.end(3):]
 data_pos=body.rfind(dm.group(1).splitlines()[0].strip());ms=list(re.finditer(rf'(?m)^\s*{re.escape(lab)}\s*$',body[:data_pos]));st=ms[-1].start();nxt=re.search(r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',body[ms[-1].end():data_pos]);en=ms[-1].end()+nxt.start() if nxt else data_pos
 seg=body[st:en];outside=body[:st]+body[en:data_pos];pres=en
 for lm in re.finditer(r'(?m)^\s*(:[A-Za-z0-9_]+)\s*$',seg):
  l=lm.group(1)
  if l.startswith(':pswitch_'):continue
  if re.search(rf'(?<![A-Za-z0-9_]){re.escape(l)}(?![A-Za-z0-9_])',outside):pres=min(pres,st+lm.start())
 return body[:st]+body[pres:]
pruned=0
for c,p in list(files.items()):
 if c in seed or not p.exists():continue
 t=p.read_text();changed_file=False
 for a,b,body in reversed(methods(t)):
  candidates=[x for x in switch_cases(body) if any(f'L{s};' in x[5] for s in seed)]
  for dm,case,lab,st,en,seg in sorted(candidates,key=lambda x:x[3],reverse=True):
   body=prune_one(body,case,lab,dm,st,en);pruned+=1
  if candidates:t=t[:a]+body+t[b:];changed_file=True
 if changed_file:p.write_text(t)
pattern='|'.join(re.escape('L'+s+';') for s in sorted(seed,key=len,reverse=True))
for c,p in list(files.items()):
 if c in seed or not p.exists():continue
 t=p.read_text();before=t
 t=re.sub(r'(?ms)^\.method[^\n]*(?:'+pattern+r')[^\n]*\n.*?^\.end method\n?','',t)
 t=re.sub(r'(?m)^\.field[^\n]*(?:'+pattern+r')[^\n]*\n','',t)
 for s in seed:t=re.sub(rf'(?m)^\.implements L{re.escape(s)};\n','',t)
 if t!=before:p.write_text(t)
def parse_args(s):
 x=s[s.find('{')+1:s.find('}')].strip()
 if '..' in x:
  a,b=[q.strip() for q in x.split('..')];ma=re.fullmatch(r'([vp])(\d+)',a);mb=re.fullmatch(r'([vp])(\d+)',b)
  if ma and mb and ma.group(1)==mb.group(1):return [ma.group(1)+str(i) for i in range(int(ma.group(2)),int(mb.group(2))+1)]
 return [q.strip() for q in x.split(',') if q.strip()]
def dr(s):
 r=REG_RE.findall(s)
 if not r:return set(),set()
 op=s.split()[0]
 if op.startswith(('const','move-result','new-instance','new-array','sget','iget','aget','instance-of')):return {r[0]},set(r[1:])
 if op.startswith('move'):return {r[0]},set(r[1:2])
 if op.startswith('invoke-'):return set(),set(parse_args(s))
 return set(),set(r)
for c,p in list(files.items()):
 if c in seed or not p.exists():continue
 t=p.read_text();out=[];last=0;fc=False
 for a,b,body in methods(t):
  ls=body.splitlines();targets=[i for i,l in enumerate(ls) if l.strip().startswith('invoke-') and any(f'L{s};->' in l for s in seed)];rem=set(targets)
  for i in targets:
   j=i+1
   while j<len(ls)-1 and (not ls[j].strip() or ls[j].lstrip().startswith(('.', '#'))):j+=1
   if j<len(ls)-1 and ls[j].strip().startswith('move-result'):rem.add(j)
  needed=set()
  for i in rem:needed|=dr(ls[i].strip())[1]
  for i in range((max(rem)-1 if rem else -1),0,-1):
   if i in rem:continue
   s=ls[i].strip()
   if s.startswith((':','goto','if-','return','throw','packed-switch','sparse-switch')):continue
   d,r=dr(s)
   if d&needed:
    safe=True
    for k in range(i+1,len(ls)-1):
     if k in rem:continue
     sk=ls[k].strip()
     if sk.startswith(':'):break
     dk,rk=dr(sk)
     if d&rk:safe=False;break
     if d&dk:break
    if safe:rem.add(i);needed=(needed-d)|r
  nb='\n'.join(l for i,l in enumerate(ls) if i not in rem)+('\n' if body.endswith('\n') else '')
  out.append(t[last:a]);out.append(nb);last=b;fc|=bool(rem)
 out.append(t[last:])
 if fc:p.write_text(''.join(out))
files,texts=load();expanded=set(seed);again=True
while again:
 again=False
 for c,t in texts.items():
  if c in expanded:continue
  src=(SOURCE_RE.search(t).group(1) if SOURCE_RE.search(t) else '')
  if not re.search(r'(?i)(metric|timing|visual.*event|notification)',src):continue
  refs={r for r in REF_RE.findall(t) if r in texts and r!=c}
  inbound=[x for x,tx in texts.items() if x not in expanded|{c} and f'L{c};' in tx]
  if refs&expanded and not inbound:expanded.add(c);again=True
for s in sorted(expanded):
 refs=[c for c,p in files.items() if c not in expanded and p.exists() and f'L{s};' in p.read_text(errors='ignore')]
 if refs:raise SystemExit(f'residual Mozc metric reference {s}: {refs[:30]}')
for s in sorted(expanded):
 if files[s].exists():files[s].unlink();print('deleted',s)
if pruned<1:raise SystemExit('expected synthetic Mozc metric branches')
print('Mozc telemetry removed: seeds',len(initial),'closure',len(expanded),'switch branches',pruned)
