#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, re, sys
ROOT=Path(sys.argv[1]); REPORT=Path(sys.argv[2])
BASE_APK_SHA='86410921a48a31d8416c92f1016a2a8177bc69053b57c1613ef3754e66ea86ba'
EXPECTED={
 'smali/uaz.smali':'29bb3df44feaa3c72b067e20ad69a948b14abf127d2dbb0edaae226f1da39c32',
 'smali/ucu.smali':'8c115b661ef6c1bd81c8398717f477da43067d1d0bd0b4c0c406e57673aac3e3',
 'smali/eoi.smali':'288aebe59c2913893db78d63f8accc7b8f7ebc19f5d1f3e6ee938569efe4888e',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def req(c,m):
    if not c: raise SystemExit('FAIL: '+m)
for rel,h in EXPECTED.items():
    p=ROOT/rel; req(p.is_file(),'missing '+rel); req(sha(p)==h,f'input drift {rel}: {sha(p)} != {h}')
texts={p.relative_to(ROOT).as_posix():p.read_text(errors='replace') for p in ROOT.rglob('*.smali')}
luaz_callers=[k for k,v in texts.items() if 'new-instance v3, Luaz;' in v or 'Luaz;-><init>' in v]
req(luaz_callers==['smali/eoi.smali'], 'unexpected Luaz construction files '+repr(luaz_callers))
eoi=texts['smali/eoi.smali']
req(eoi.count('Luaz;-><init>(Laals;Laals;Laals;Laals;Laals;Laals;Laals;Laals;Laals;Laals;Laals;I[B)V')==1,'Luaz ctor call count drift')
site=re.search(r'new-instance v3, Luaz;(?s:.{0,240})const/4 v15, 0x1(?s:.{0,900})Luaz;-><init>\(Laals;Laals;Laals;Laals;Laals;Laals;Laals;Laals;Laals;Laals;Laals;I\[B\)V',eoi)
req(site is not None,'cannot prove Luaz selector 1 construction')
uaz=texts['smali/uaz.smali']
pro='''    const/4 v1, 0x1\n\n    .line 6\n    if-eq v0, v1, :cond_0\n'''
start=uaz.find(pro); req(start>=0,'Luaz selector dispatch prologue drift')
start += len(pro)
end=uaz.find('    :cond_0\n',start); req(end>start,'Luaz default branch end missing')
block=uaz[start:end]
req('new-instance v2, Lucp;' in block and 'Lucp;-><init>(Lpol;Lucl;Lwzg;Laajo;Luct;Ltwg;Labjb;Ljava/util/concurrent/Executor;Lvow;)V' in block,'Luaz default is not memory-service branch')
ucu_refs=sorted(k for k,v in texts.items() if 'Lucu;' in v)
req(ucu_refs==['smali/ucu.smali'], 'unexpected Lucu refs '+repr(ucu_refs))
replacement='''\n    new-instance v0, Ljava/lang/UnsupportedOperationException;\n\n    const-string v1, "Removed Primes memory reporter provider branch"\n\n    invoke-direct {v0, v1}, Ljava/lang/UnsupportedOperationException;-><init>(Ljava/lang/String;)V\n\n    throw v0\n\n'''
uaz2=uaz[:start]+replacement+uaz[end:]
(ROOT/'smali/uaz.smali').write_text(uaz2)
(ROOT/'smali/ucu.smali').unlink()
texts2={p.relative_to(ROOT).as_posix():p.read_text(errors='replace') for p in ROOT.rglob('*.smali')}
joined='\n'.join(texts2.values())
req('Lucu;' not in joined,'Lucu descriptor remains')
req('new-instance v2, Lucp;' not in texts2['smali/uaz.smali'],'memory service construction survived in Luaz')
for marker in ['org.futo.voiceinput.moonshine','Lcom/mekromn/meboard/VoiceProviderRelayActivity;','Test Meboard']:
    req(marker in joined,'locked feature missing '+marker)
for marker in ['Lrqw;','Lpsa;','Lpsp;','Lmck;','Lmcj;','Lkgd;','Lkgb;','Lkga;','Lkfu;','Lkfy;','Lkfw;','Lkfx;','Lkfv;','Luda;','Lucy;']:
    req(marker not in joined,'locked removal returned '+marker)
for marker in ['Lucp;','Luct;','MemoryUsageCapture.java']:
    req(marker in joined,'memory implementation unexpectedly absent '+marker)
REPORT.write_text(json.dumps({
 'base_stage':50,
 'base_apk_sha256':BASE_APK_SHA,
 'deleted_classes':['ucu'],
 'modified_classes':['uaz'],
 'removed_scope':'unreachable Primes memory-service provider branch + unreferenced MemoryUsageCapture provider',
 'retained_boundary':'memory reporter implementation remains packaged for next runtime-gated stage; local memory-pressure/stability behavior untouched',
 'runtime_tested':False,'privacy_final':False
},indent=2)+'\n')
print('PASS stage51 memory factory patch')
