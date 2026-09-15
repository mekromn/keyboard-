#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, re, sys
ROOT=Path(sys.argv[1]); REPORT=Path(sys.argv[2])
BASE_APK_SHA='229223d8a27ecdc5196079533a834cbe5d8ecebf5292ea407e8cdaf6e3c06ca5'
EXPECTED={
 'smali/ucp.smali':'4f85dd59b3f12f1f0346c26d82942207722ed82f188a9f212381a5618fc83e9e',
 'smali/ucn.smali':'4d42ed32a67dd05490e417040bfd2b2824fa6f83736505d25b720d8f068fb500',
 'smali/uco.smali':'d4b427b2ddb015d0af0514435dd72d051d893865f743834a8c659ffb49c258ed',
 'smali/uch.smali':'bdaff85bf0cde0c2b14a0c99b910a2df0442995111a2cbbb460d4836e79c5523',
 'smali/ucr.smali':'a38a200a95d6926eed7f48235e7144de9ba8664b89d06d3d7a6df4045a25bbb2',
 'smali/ucs.smali':'b6ece22f500b062de3edf9cb2746556f0c016b4235e13b17042e4d0d1b083633',
 'smali/uqx.smali':'8b94d0170116226aa90978e56da60723f4b1a17313fe2204b91b9fb0e5b98825',
}
DELETED=['ucp','ucn','uco','uch','ucr','ucs']

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def req(c,m):
    if not c: raise SystemExit('FAIL: '+m)
for rel,h in EXPECTED.items():
    p=ROOT/rel; req(p.is_file(),'missing '+rel); req(sha(p)==h,f'input drift {rel}: {sha(p)} != {h}')
texts={p.relative_to(ROOT).as_posix():p.read_text(errors='replace') for p in ROOT.rglob('*.smali')}
# Closed service graph proof after Stage 51 factory cut.
refs={}
for c in DELETED:
    d='L'+c+';'
    refs[c]=sorted(k for k,v in texts.items() if d in v and k!=f'smali/{c}.smali')
expected_refs={
 'ucp':['smali/ucn.smali','smali/uco.smali','smali/uqx.smali'],
 'ucn':['smali/ucp.smali'],
 'uco':['smali/uqx.smali'],
 'uch':['smali/ucp.smali'],
 'ucr':['smali/uco.smali'],
 'ucs':['smali/uco.smali'],
}
req(refs==expected_refs,'memory service graph drift '+repr(refs))
# Stage 51 must already have removed all Lucp construction from Luaz and globally.
req(not any('new-instance' in line and 'Lucp;' in line for v in texts.values() for line in v.splitlines()),'Lucp still directly constructed')
# Uqx has exactly one memory-only constructor and one surviving unrelated constructor.
uqx=texts['smali/uqx.smali']
mem_ctor=re.search(r'(?ms)^\.method public synthetic constructor <init>\(Lucp;ILjava/lang/String;Ljava/lang/String;I\)V\n.*?^\.end method\n?',uqx)
req(mem_ctor is not None,'memory Uqx ctor missing')
req(uqx.count('.method public synthetic constructor <init>')==2,'Uqx ctor count drift')
# The only surviving Uqx constructor site is the unrelated Luqy branch and selector 0.
ctors=[]
for k,v in texts.items():
    if 'Luqx;-><init>' in v: ctors.append((k,v.count('Luqx;-><init>')))
req(sorted(ctors)==[('smali/gdg.smali',1),('smali/ucp.smali',1)],'Uqx construction sites drift '+repr(ctors))
gdg=texts['smali/gdg.smali']
req('Luqx;-><init>(Luqy;Lzuk;ILjava/util/List;I)V' in gdg,'surviving Uqx ctor missing')
req(re.search(r'const/4 v7, 0x0(?s:.{0,180})invoke-direct/range \{v2 \.\. v7\}, Luqx;-><init>\(Luqy;Lzuk;ILjava/util/List;I\)V',gdg) is not None,'cannot prove surviving Uqx selector 0')
# Remove memory constructor and memory branch of a(), retaining exact unrelated branch.
uqx2=uqx[:mem_ctor.start()]+uqx[mem_ctor.end():]
m=re.search(r'(?ms)^\.method public final a\(\)Lwzc;\n.*?^\.end method\n?',uqx2)
req(m is not None,'Uqx a() missing')
body=m.group(0)
idx=body.find('    :cond_3\n'); req(idx>=0,'Uqx unrelated branch label missing')
tail=body[idx+len('    :cond_3\n'):body.rfind('.end method')]
new_method='.method public final a()Lwzc;\n    .locals 8\n\n    const/4 v1, 0x1\n\n'+tail+'.end method\n'
uqx2=uqx2[:m.start()]+new_method+uqx2[m.end():]
(ROOT/'smali/uqx.smali').write_text(uqx2)
for c in DELETED:
    (ROOT/f'smali/{c}.smali').unlink()
# End-state references and cumulative gates.
texts2={p.relative_to(ROOT).as_posix():p.read_text(errors='replace') for p in ROOT.rglob('*.smali')}
joined='\n'.join(texts2.values())
for c in DELETED:
    req('L'+c+';' not in joined,'deleted descriptor remains L'+c+';')
req('Lucp;' not in texts2['smali/uqx.smali'],'Uqx memory service branch remains')
req('Luqx;-><init>(Lucp;' not in joined,'memory Uqx constructor remains')
# Keep shared memory utilities/configuration for later classification.
for marker in ['Luct;','Lucg;','MemoryUsageCapture.java']:
    req(marker in joined,'shared memory utility unexpectedly removed '+marker)
# Locked cumulative features/removals.
for marker in ['org.futo.voiceinput.moonshine','Lcom/mekromn/meboard/VoiceProviderRelayActivity;','Test Meboard']:
    req(marker in joined,'locked feature missing '+marker)
for marker in ['Lrqw;','Lpsa;','Lpsp;','Lmck;','Lmcj;','Lkgd;','Lkgb;','Lkga;','Lkfu;','Lkfy;','Lkfw;','Lkfx;','Lkfv;','Luda;','Lucy;','Ltwk;','Lucu;']:
    req(marker not in joined,'locked removal returned '+marker)
REPORT.write_text(json.dumps({
 'base_stage':51,
 'base_apk_sha256':BASE_APK_SHA,
 'deleted_classes':DELETED,
 'modified_classes':['uqx'],
 'removed_scope':'unconstructible Primes MemoryMetricServiceImpl service + private callbacks/state/proc-memory continuation helpers',
 'retained_boundary':'MemoryUsageCapture/shared memory configuration utilities remain because they have surviving non-service callers and require separate classification',
 'runtime_tested':False,'privacy_final':False
},indent=2)+'\n')
print('PASS stage52 memory service patch')
