#!/usr/bin/env python3
"""Physically remove LegacyClearcutAdapter while retaining qdb's unrelated listeners."""
from pathlib import Path
import re
ROOT=Path('/mnt/data/meboard_work/buildtree')

def find(c):
 h=list(ROOT.glob(f'smali*/**/{c}.smali'))
 if len(h)!=1:raise SystemExit((c,h))
 return h[0]
p=find('inr');t=p.read_text();meth=re.search(r'(?ms)^\.method public final synthetic iM\(\)Ljava/lang/Object;\n.*?^\.end method',t,re.M)
if not meth:raise SystemExit('inr iM missing')
b=meth.group(0);dm=re.search(r'(?ms)(:pswitch_data_0\s*\n\s*\.packed-switch\s+0x([0-9a-f]+)\s*\n)(.*?)(\s*\.end packed-switch)',b)
base=int(dm.group(2),16);labs=re.findall(r':pswitch_[0-9a-f]+',dm.group(3));cmap={base+i:l for i,l in enumerate(labs)}
case=17;lab=cmap[case];repl=cmap[16];data=dm.group(3);data=re.sub(rf'(?m)^(\s*){re.escape(lab)}\s*$',rf'\1{repl}',data,count=1)
b=b[:dm.start(3)]+data+b[dm.end(3):];dp=b.rfind(':pswitch_data_0');ms=list(re.finditer(rf'(?m)^\s*{re.escape(lab)}\s*$',b[:dp]));st=ms[-1].start();nxt=re.search(r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',b[ms[-1].end():dp]);en=ms[-1].end()+nxt.start() if nxt else dp
b=b[:st]+b[en:];t=t[:meth.start()]+b+t[meth.end():];p.write_text(t)
p=find('qdb');t=p.read_text();pat=re.compile(r'(?ms)^\.method public constructor <init>\(Lpsn;I\)V\n.*?^\.end method\n?');t,n=pat.subn('',t,count=1)
if n!=1:raise SystemExit('qdb psn constructor missing')
m=re.search(r'(?ms)^\.method public final synthetic dT\(Ljava/lang/Class;\)V\n.*?^\.end method',t,re.M);b=m.group(0)
needle='    const/4 p1, 0x1\n\n    .line 6\n    if-eq p0, p1, :cond_1\n\n    .line 7\n    .line 8\n'
if needle not in b:raise SystemExit('qdb dT case1 dispatch missing')
b=b.replace(needle,'    .line 7\n    .line 8\n',1);r=re.search(r'(?ms)^\s*:cond_1\s*$.*?(?=^\s*:cond_2\s*$)',b,re.M)
if not r:raise SystemExit('qdb dT cond1 body missing')
b=b[:r.start()]+b[r.end():];t=t[:m.start()]+b+t[m.end():]
m=re.search(r'(?ms)^\.method public final synthetic dU\(Lpyj;\)V\n.*?^\.end method',t,re.M);b=m.group(0)
needle='    const/4 v0, 0x1\n\n    .line 8\n    if-eq v1, v0, :cond_3\n\n    .line 9\n    .line 10\n'
if needle not in b:raise SystemExit('qdb dU case1 dispatch missing')
b=b.replace(needle,'    .line 9\n    .line 10\n',1);r=re.search(r'(?ms)^\s*:cond_3\s*$.*?(?=^\s*:cond_5\s*$)',b,re.M)
if not r:raise SystemExit('qdb dU cond3 body missing')
b=b[:r.start()]+b[r.end():];t=t[:m.start()]+b+t[m.end():];p.write_text(t)
psn=find('psn');refs=[str(f.relative_to(ROOT)) for f in ROOT.glob('smali*/**/*.smali') if f!=psn and 'Lpsn;' in f.read_text(errors='ignore')]
if refs:raise SystemExit(f'psn still referenced {refs[:20]}')
psn.unlink();print('LegacyClearcutAdapter implementation and all factory/listener branches removed')
