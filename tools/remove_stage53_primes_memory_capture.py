#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, re, sys
ROOT=Path(sys.argv[1]); REPORT=Path(sys.argv[2])
BASE_APK_SHA='6c3cad70f13fd229db0820991a5519bd4663277c45733a4604cdb3a89f13d739'
EXPECTED={
 'smali/uct.smali':'2e7139ce8d2889d8b8275e6134748aa6822259f5d8b46ed6dd9bb0e60dfe9a30',
 'smali/ucq.smali':'0b0beefeb695bb2f569f411a0bb5ef1c57cc48e035ec200ff17480ed74d4e5d6',
 'smali/pdh.smali':'2e61306eceb98b479849100c944ea5c16969557df60070d8d31137f48d94b657',
 'smali/trn.smali':'e7bd3efd8a99172adaea8f50fdaf9defa1acfdb0ada2a473aa9d4373945d6ac8',
}
DELETED=['uct','ucq']

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def req(c,m):
    if not c: raise SystemExit('FAIL: '+m)
for rel,h in EXPECTED.items():
    p=ROOT/rel; req(p.is_file(),'missing '+rel); req(sha(p)==h,f'input drift {rel}: {sha(p)} != {h}')
texts={p.relative_to(ROOT).as_posix():p.read_text(errors='replace') for p in ROOT.rglob('*.smali')}
joined='\n'.join(texts.values())
req('Luct;-><init>' not in joined,'MemoryUsageCapture unexpectedly has constructor callers')
refs={}
for c in DELETED:
    d='L'+c+';'
    refs[c]=sorted(k for k,v in texts.items() if d in v and k!=f'smali/{c}.smali')
expected_refs={
 'uct':['smali/pdh.smali','smali/trn.smali','smali/ucq.smali'],
 'ucq':['smali/uct.smali'],
}
req(refs==expected_refs,'capture graph drift '+repr(refs))
pdh_sites=[]
for k,v in texts.items():
    lines=v.splitlines()
    for i,line in enumerate(lines):
        if 'Lpdh;-><init>(I)V' in line:
            m=re.search(r'invoke-direct \{([^}]+)\}',line)
            if not m: continue
            regs=[x.strip() for x in m.group(1).split(',')]
            if len(regs)!=2: continue
            sel=regs[1]
            val=None
            for prev in reversed(lines[max(0,i-10):i]):
                mm=re.search(r'\bconst(?:/4|/16)?\s+'+re.escape(sel)+r',\s*(-?0x[0-9a-fA-F]+|-?\d+)',prev)
                if mm:
                    val=int(mm.group(1),0); break
            if val==9: pdh_sites.append(k)
req(pdh_sites==['smali/uct.smali'],'pdh selector-9 construction drift '+repr(pdh_sites))
def switch_label(text, selector):
    m=re.search(r'\.packed-switch\s+0x0\n(?P<body>.*?)\.end packed-switch',text,re.S)
    req(m is not None,'packed switch missing')
    labs=re.findall(r':pswitch_[0-9a-f]+',m.group('body'))
    req(selector < len(labs),'selector out of range')
    return labs[selector]
req(switch_label(texts['smali/pdh.smali'],9)==':pswitch_4','pdh selector 9 mapping drift')
req(switch_label(texts['smali/trn.smali'],6)==':pswitch_9','trn selector 6 mapping drift')
pdh=texts['smali/pdh.smali']
pdh_old=re.search(r'(?ms)^    :pswitch_4\n.*?(?=^    :pswitch_5\n)',pdh)
req(pdh_old is not None and 'Luct;->b()Lvow;' in pdh_old.group(0),'pdh capture branch missing/drifted')
pdh_new='''    :pswitch_4\n    new-instance p0, Ljava/lang/UnsupportedOperationException;\n\n    const-string v0, "Removed Primes MemoryUsageCapture provider"\n\n    invoke-direct {p0, v0}, Ljava/lang/UnsupportedOperationException;-><init>(Ljava/lang/String;)V\n\n    throw p0\n\n'''
pdh=pdh[:pdh_old.start()]+pdh_new+pdh[pdh_old.end():]
(ROOT/'smali/pdh.smali').write_text(pdh)
trn=texts['smali/trn.smali']
trn_old=re.search(r'(?ms)^    :pswitch_9\n.*?(?=^    :pswitch_a\n)',trn)
req(trn_old is not None and 'check-cast v0, Luct;' in trn_old.group(0),'trn Luct branch missing/drifted')
trn_new='''    :pswitch_9\n    new-instance v0, Ljava/lang/UnsupportedOperationException;\n\n    const-string v1, "Removed Primes MemoryUsageCapture branch"\n\n    invoke-direct {v0, v1}, Ljava/lang/UnsupportedOperationException;-><init>(Ljava/lang/String;)V\n\n    throw v0\n\n'''
trn=trn[:trn_old.start()]+trn_new+trn[trn_old.end():]
(ROOT/'smali/trn.smali').write_text(trn)
for c in DELETED:
    (ROOT/f'smali/{c}.smali').unlink()
texts2={p.relative_to(ROOT).as_posix():p.read_text(errors='replace') for p in ROOT.rglob('*.smali')}
joined2='\n'.join(texts2.values())
for c in DELETED:
    req('L'+c+';' not in joined2,'deleted descriptor remains L'+c+';')
for marker in ['MemoryUsageCapture.java','com/google/android/libraries/performance/primes/metrics/memory/MemoryUsageCapture']:
    req(marker not in joined2,'capture marker remains '+marker)
for marker in ['Lucl;','Lucj;','Luck;','Lucg;','Lucv;']:
    req(marker in joined2,'retained shared memory machinery unexpectedly removed '+marker)
for marker in ['org.futo.voiceinput.moonshine','Lcom/mekromn/meboard/VoiceProviderRelayActivity;','Test Meboard']:
    req(marker in joined2,'locked feature missing '+marker)
for marker in ['Lrqw;','Lpsa;','Lpsp;','Lmck;','Lmcj;','Lkgd;','Lkgb;','Lkga;','Lkfu;','Lkfy;','Lkfw;','Lkfx;','Lkfv;','Luda;','Lucy;','Ltwk;','Lucu;','Lucp;','Lucn;','Luco;','Luch;','Lucr;','Lucs;']:
    req(marker not in joined2,'locked removal returned '+marker)
REPORT.write_text(json.dumps({
 'base_stage':52,
 'base_apk_sha256':BASE_APK_SHA,
 'deleted_classes':DELETED,
 'modified_classes':['pdh','trn'],
 'removed_scope':'orphaned Primes MemoryUsageCapture implementation + private config-combiner helper; shared synthetic branches that referenced deleted capture replaced by explicit unreachable boundaries',
 'retained_boundary':'ucl/ucj memory-state machinery, ucg configuration and ucv shared supplier remain because they have independent callers',
 'runtime_tested':False,
 'privacy_final':False
},indent=2)+'\n')
print('PASS stage53 Primes MemoryUsageCapture patch')
