#!/usr/bin/env python3
"""Delete closed background/reporting network client components.

Consumes audit_network_surface JSON. A component is eligible only when every
class in its SCC is classified as background/reporting and no retained class,
manifest/resource entry, or reflective class-name string reaches the SCC.
User-feature and unclassified transports are never selected automatically.
"""
from __future__ import annotations
from pathlib import Path
import argparse,json,re
from collections import defaultdict
CLASS_RE=re.compile(r'^\.class[^\n]* L([^;]+);',re.M)
REF_RE=re.compile(r'L([A-Za-z0-9_$/]+);')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('root',type=Path,nargs='?',default=Path('/mnt/data/meboard_work/buildtree'));ap.add_argument('--report',type=Path,default=Path('/mnt/data/meboard_network_surface.json'));a=ap.parse_args();root=a.root
 r=json.loads(a.report.read_text());candidate={x['class'] for x in r['java_smali_findings'] if x['classification']=='background_or_reporting'}
 files={};texts={}
 for p in root.glob('smali*/**/*.smali'):
  t=p.read_text(errors='ignore');m=CLASS_RE.search(t)
  if m:files[m.group(1)]=p;texts[m.group(1)]=t
 candidate&=set(files);g=defaultdict(set);rev=defaultdict(set)
 for c,t in texts.items():
  for d in set(REF_RE.findall(t))-{c}:
   if d in texts:g[c].add(d);rev[d].add(c)
 idx={};low={};stack=[];on=set();counter=0;scc=[]
 def strong(v):
  nonlocal counter
  idx[v]=low[v]=counter;counter+=1;stack.append(v);on.add(v)
  for w in g[v]&candidate:
   if w not in idx:strong(w);low[v]=min(low[v],low[w])
   elif w in on:low[v]=min(low[v],idx[w])
  if low[v]==idx[v]:
   comp=set()
   while True:
    w=stack.pop();on.remove(w);comp.add(w)
    if w==v:break
   scc.append(comp)
 for v in sorted(candidate):
  if v not in idx:strong(v)
 other=[]
 for p in root.rglob('*'):
  if not p.is_file() or p.suffix in {'.smali','.so','.dex','.arsc'} or 'build' in p.relative_to(root).parts:continue
  try:other.append((p,p.read_text(errors='ignore')))
  except OSError:pass
 eligible=[]
 for comp in scc:
  inbound=set().union(*(rev[c]-comp for c in comp))
  if inbound:continue
  reflect=False
  for c in comp:
   dot=c.replace('/','.')
   if any(c in t or dot in t for _,t in other):reflect=True;break
  if not reflect:eligible.append(comp)
 removed=[]
 for comp in eligible:
  for c in sorted(comp):files[c].unlink();removed.append(c);print('deleted orphan background client',c)
 if not removed:raise SystemExit('no closed background network client SCCs')
 for c in removed:
  hits=[str(p.relative_to(root)) for p in root.glob('smali*/**/*.smali') if f'L{c};' in p.read_text(errors='ignore')]
  if hits:raise SystemExit(f'residual {c}: {hits[:20]}')
 print('removed',len(removed),'classes in',len(eligible),'closed background-network SCCs')
if __name__=='__main__':main()
