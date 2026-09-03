#!/usr/bin/env python3
"""Remove the remaining named Primes/Clearcut/native-crash implementation cluster.

Run after the earlier Meboard telemetry pruning/Dagger DCE stages. The script uses
exact switch cases for this Gboard 18.0.3 build and aborts on unexpected references.
"""
from pathlib import Path
import re, xml.etree.ElementTree as ET
ROOT=Path('/mnt/data/meboard_work/buildtree')
ANDROID='{http://schemas.android.com/apk/res/android}'
CASES={'pch':{16}, 'ter':{12}, 'sdy':{17}, 'rhg':{4}}

def find(cls):
    hits=list(ROOT.glob(f'smali*/**/{cls}.smali'))
    if len(hits)!=1: raise SystemExit(f'{cls}: expected one file, got {hits}')
    return hits[0]

def methods(text):
    out=[];pos=0
    while True:
        m=re.search(r'^\.method[^\n]*\n',text[pos:],re.M)
        if not m:break
        a=pos+m.start();b=text.find('\n.end method',pos+m.end())
        if b<0:raise SystemExit('unterminated method')
        b+=len('\n.end method');out.append((a,b,text[a:b]));pos=b
    return out

def prune_switch(body, removed):
    dm=re.search(r'(?ms)^\s*:pswitch_data_0\s*\n\s*\.packed-switch\s+0x([0-9a-f]+)\s*\n(.*?)^\s*\.end packed-switch',body,re.M)
    if not dm:return body,0
    base=int(dm.group(1),16);labs=re.findall(r':pswitch_[0-9a-f]+',dm.group(2));cmap={base+i:l for i,l in enumerate(labs)}
    rem=set(removed)&set(cmap)
    if not rem:return body,0
    keep=[c for c in cmap if c not in rem]
    if not keep:raise SystemExit('cannot remove all switch cases')
    repl=cmap[keep[0]];data=dm.group(2)
    for c in rem:data=re.sub(rf'(?m)^(\s*){re.escape(cmap[c])}\s*$',rf'\1{repl}',data,count=1)
    body=body[:dm.start(2)]+data+body[dm.end(2):]
    data_pos=body.rfind(':pswitch_data_0');ranges=[]
    for c in rem:
        lab=cmap[c];ms=list(re.finditer(rf'(?m)^\s*{re.escape(lab)}\s*$',body[:data_pos]))
        if not ms:raise SystemExit(f'case {c} body {lab} missing')
        st=ms[-1].start();nxt=re.search(r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',body[ms[-1].end():data_pos]);en=ms[-1].end()+nxt.start() if nxt else data_pos
        seg=body[st:en];preserve=en
        for lm in re.finditer(r'(?m)^\s*(:[A-Za-z0-9_]+)\s*$',seg):
            lab2=lm.group(1)
            if lab2.startswith(':pswitch_'):continue
            outside=body[:st]+body[en:data_pos]
            if re.search(rf'(?<![A-Za-z0-9_]){re.escape(lab2)}(?![A-Za-z0-9_])',outside):preserve=min(preserve,st+lm.start())
        ranges.append((st,preserve))
    for st,en in sorted(ranges,reverse=True):body=body[:st]+body[en:]
    return body,len(ranges)

for cls,rem in CASES.items():
    p=find(cls);t=p.read_text();changed=0
    for a,b,body in reversed(methods(t)):
        if 'packed-switch' not in body:continue
        nb,n=prune_switch(body,rem)
        if n:t=t[:a]+nb+t[b:];changed+=n
    if changed!=len(rem):raise SystemExit(f'{cls}: expected {len(rem)} removed branch, got {changed}')
    p.write_text(t)

tfh=find('tfh');t=tfh.read_text()
needle='''    const/4 v1, 0x3\n\n    .line 15\n    if-eq v0, v1, :cond_0\n\n    .line 16\n    .line 17\n'''
if needle not in t:raise SystemExit('tfh discriminator-3 dispatch anchor missing')
t=t.replace(needle,'    .line 16\n    .line 17\n',1)
m=re.search(r'(?ms)^\s*:cond_0\s*$.*?(?=^\s*:cond_3\s*$)',t,re.M)
if not m:raise SystemExit('tfh Primes branch body missing')
t=t[:m.start()]+t[m.end():];tfh.write_text(t)

uff=find('uff');t=uff.read_text()
pat=re.compile(r'(?ms)^\.method public constructor <init>\(Landroid/content/Context;Lvow;Lufc;Lcom/google/android/libraries/performance/primes/transmitter/clearcut/ClearcutMetricSnapshotTransmitter;\)V\n.*?^\.end method\n?')
t,n=pat.subn('',t,count=1)
if n!=1:raise SystemExit('Clearcut-only Luff constructor missing')
uff.write_text(t)

manifest=ROOT/'AndroidManifest.xml'; ET.register_namespace('android','http://schemas.android.com/apk/res/android')
tree=ET.parse(manifest);app=tree.getroot().find('application');removed=0
for child in list(app):
    if child.get(ANDROID+'name')=='android.net.http.MetaDataHolder':app.remove(child);removed+=1
if removed!=1:raise SystemExit(f'expected one android.net.http.MetaDataHolder, got {removed}')
tree.write(manifest,encoding='utf-8',xml_declaration=True)

DELETE=['com/google/android/libraries/performance/primes/metrics/crash/NativeCrashHandlerImpl','com/google/android/libraries/performance/primes/transmitter/clearcut/ClearcutMetricSnapshotTransmitter','com/google/android/libraries/performance/primes/transmitter/LifeboatReceiver','ufe','uas','uan','ual','uak','uam']
classes={}
for p in ROOT.glob('smali*/**/*.smali'):
    tx=p.read_text(errors='ignore');mm=re.search(r'^\.class[^\n]* L([^;]+);',tx,re.M)
    if mm:classes[mm.group(1)]=(p,tx)
D=set(DELETE)
for c in DELETE:
    if c not in classes:raise SystemExit(f'{c} missing before deletion')
    external=[x for x,(_,tx) in classes.items() if x not in D and f'L{c};' in tx]
    if external:raise SystemExit(f'{c} still externally referenced by {external[:20]}')
for c in DELETE:classes[c][0].unlink()
so=ROOT/'lib/arm64-v8a/libnative_crash_handler_jni.so'
if not so.exists():raise SystemExit('native crash JNI library missing')
so.unlink()
for p in ROOT.glob('smali*/**/*.smali'):
    tx=p.read_text(errors='ignore')
    for c in DELETE:
        if f'L{c};' in tx:raise SystemExit(f'dangling {c} in {p.relative_to(ROOT)}')
print('remaining named Primes/native-crash cluster physically removed')
