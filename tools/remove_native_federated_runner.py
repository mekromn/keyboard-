#!/usr/bin/env python3
from pathlib import Path
import re
R=Path('/mnt/data/meboard_work/buildtree')
impl=R/'smali_classes2/com/google/android/gms/learning/dynamite/training/InAppTrainingServiceImpl.smali'
s=impl.read_text()
# Mixed static worker: delete only contiguous FL branch before :cond_1f; preserve LC branch.
ms=s.index('.method public static synthetic $r8$lambda$elG7aL0nNheYE8qgOgTttDQpQnY')
me=s.index('\n.end method',ms)+len('\n.end method')
b=s[ms:me];needle='    if-ne v5, v11, :cond_1f\n';a=b.index(needle);bs=a+len(needle);e=b.index('    :cond_1f\n',bs);region=b[bs:e]
assert 'NativeFLRunnerWrapper' in region and 'NativeLCRunnerWrapper' not in region
labels=set(re.findall(r'(?m)^\s*(:[A-Za-z0-9_]+)\s*$',region));outside=b[:bs]+b[e:]
for lab in labels:
 if re.search(rf'(?<![A-Za-z0-9_]){re.escape(lab)}(?![A-Za-z0-9_])',outside): raise SystemExit(f'FL internal label externally referenced {lab}')
b=b[:a]+'    goto/16 :cond_1f\n\n'+b[e:];s=s[:ms]+b+s[me:]
# Public FL API method gone.
s,n=re.subn(r'(?ms)^\.method public runFlTraining\(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ltir;Ltiw;\[BLljn;J\[B\)V\n.*?^\.end method\n?','',s,count=1)
if n!=1: raise SystemExit(f'runFlTraining {n}')
impl.write_text(s)
# Dedicated FL wrapper and callback.
for rel in ['smali_classes3/tjj.smali','smali_classes3/com/google/android/libraries/micore/learning/training/nflrunner/NativeFLRunnerWrapper.smali']:
 p=R/rel
 if not p.exists(): raise SystemExit(rel+' missing')
 p.unlink()
# Binder implementation: transaction 2 and its f(...) bridge.
p=R/'smali_classes2/ljj.smali';s=p.read_text()
s,n=re.subn(r'(?ms)    const/4 v1, 0x2\n\n    \.line 4\n    const/4 v2, 0x1\n.*?    if-eq v0, v1, :cond_a\n', '    const/4 v2, 0x1\n\n', s, count=1)
if n!=1:
 s,n1=re.subn(r'(?m)^\s*const/4 v1, 0x2\n','',s,count=1);s,n2=re.subn(r'(?m)^\s*if-eq v0, v1, :cond_a\n','',s,count=1)
 if n1!=1 or n2!=1: raise SystemExit(f'ljj transaction2 dispatch {n}/{n1}/{n2}')
s,n=re.subn(r'(?ms)^    :cond_a\n.*?(?=^    :goto_8\n)','',s,count=1)
if n!=1: raise SystemExit('ljj cond_a body')
s,n=re.subn(r'(?ms)^\.method public final f\(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;IZZZ\[BLljn;J\[B\)V\n.*?^\.end method\n?','',s,count=1)
if n!=1: raise SystemExit('ljj f method')
p.write_text(s)
# Controller interface no longer exposes FL RPC.
p=R/'smali_classes2/ljk.smali';s=p.read_text();s,n=re.subn(r'(?ms)^\.method public abstract f\(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;IZZZ\[BLljn;J\[B\)V\n\.end method\n?','',s,count=1)
if n!=1: raise SystemExit('ljk f method')
p.write_text(s)
allsm='\n'.join(x.read_text(errors='ignore') for x in R.glob('smali*/**/*.smali'))
if 'NativeFLRunnerWrapper' in allsm: raise SystemExit('NativeFLRunnerWrapper refs remain')
if 'runFlTraining' in allsm: raise SystemExit('runFlTraining refs remain')
if 'NativeLCRunnerWrapper' not in allsm: raise SystemExit('local runner missing')
print('Native FL runner/API physically removed; NativeLCRunnerWrapper retained')
