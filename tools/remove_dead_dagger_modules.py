#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path('/mnt/data/meboard_work/buildtree')
MAP={
 'onm':'onn','plx':'ply','noa':'nob','psu':'psv','hzh':'hzi',
 'qth':'qti','rdk':'rdl','rnm':'rnn','rrk':'rrl','nap':'naq','gqs':'gqt',
 'nwt':'nwu','oap':'oaq','hco':'hcp','hnj':'hnk','hup':'huq','evj':'evk',
 'ifw':'ifx','igd':'ige','joh':'joi','igi':'igj','jpp':'jpq','rgv':'rgw','kbn':'kbo',
}

def class_files():
    out={}
    for p in ROOT.glob('smali*/**/*.smali'):
        t=p.read_text(errors='ignore')
        m=re.search(r'^\.class[^\n]* L([^;]+);',t,re.M)
        if m: out[m.group(1)]=(p,t)
    return out
classes=class_files()
eqp,eqt=classes['eqt']
for target,iface in MAP.items():
    assert target in classes and iface in classes, (target,iface)
    refs_t=[c for c,(p,t) in classes.items() if c!=target and f'L{target};' in t]
    refs_i=[c for c,(p,t) in classes.items() if c!=iface and f'L{iface};' in t]
    if set(refs_t)-{'eqt',iface}:
        raise SystemExit(f'{target} unexpected inbound {refs_t}')
    if set(refs_i)-{'eqt'}:
        raise SystemExit(f'{iface} unexpected inbound {refs_i}')
    it=classes[iface][1]
    mm=re.findall(r'^\.method public abstract ([^\n]+)$',it,re.M)
    if len(mm)!=1 or not mm[0].endswith(f')L{target};'):
        raise SystemExit(f'{iface} unexpected methods {mm}')
    sig=mm[0]
    pat=re.compile(rf'(?ms)^\.method public final {re.escape(sig)}\n.*?^\.end method\n?')
    eqt,n=pat.subn('',eqt,count=1)
    if n!=1: raise SystemExit(f'eqt method {sig} not uniquely found')
    eqt,n=re.subn(rf'(?m)^\.implements L{re.escape(iface)};\n','',eqt,count=1)
    if n!=1: raise SystemExit(f'eqt implements {iface} not found')
    print('remove',iface,sig,'and target',target)
eqp.write_text(eqt)
for target,iface in MAP.items():
    classes[target][0].unlink(); classes[iface][0].unlink()
print('removed',len(MAP),'dead Dagger metric module/interface pairs')
