#!/usr/bin/env python3
from pathlib import Path
import re
p=Path('/mnt/data/meboard_work/buildtree/smali/rse.smali'); text=p.read_text(); REMOVE={8,9,10}
dm=re.search(r'(?ms)(^\s*:pswitch_data_0\s*\n\s*\.packed-switch\s+0x([0-9a-f]+)\s*\n)(.*?)(^\s*\.end packed-switch)',text,re.M)
if not dm:raise SystemExit('table missing')
base=int(dm.group(2),16);labels=re.findall(r':pswitch_[0-9a-f]+',dm.group(3));cmap={base+i:l for i,l in enumerate(labels)}
repl=cmap[7];data=dm.group(3)
for c in REMOVE:data=re.sub(rf'(?m)^(\s*){re.escape(cmap[c])}\s*$',rf'\1{repl}',data,count=1)
text=text[:dm.start(3)]+data+text[dm.end(3):]; data_pos=text.rindex(':pswitch_data_0')
ranges=[]
for c in REMOVE:
 lab=cmap[c];ms=list(re.finditer(rf'(?m)^\s*{re.escape(lab)}\s*$',text[:data_pos]))
 if not ms:raise SystemExit((c,lab))
 st=ms[-1].start();nxt=re.search(r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',text[ms[-1].end():data_pos]);en=ms[-1].end()+nxt.start() if nxt else data_pos
 seg=text[st:en];preserve=en
 for lm in re.finditer(r'(?m)^\s*(:[A-Za-z0-9_]+)\s*$',seg):
  l2=lm.group(1)
  if l2.startswith(':pswitch_'):continue
  if re.search(rf'(?<![A-Za-z0-9_]){re.escape(l2)}(?![A-Za-z0-9_])',text[:st]+text[en:data_pos]):preserve=min(preserve,st+lm.start())
 ranges.append((st,preserve))
for st,en in sorted(ranges,reverse=True):text=text[:st]+text[en:]
p.write_text(text)
print('removed rse cases',sorted(REMOVE))
