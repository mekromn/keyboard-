#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, re, sys

ROOT=Path(sys.argv[1])
REPORT=Path(sys.argv[2])
BASE_APK_SHA='b65613b116dc017e3bc8054992089ebffe4544149e9c93cec085c302ad2628ed'
EXPECTED={
 'smali_classes3/uda.smali':'282d58cc9f7b14b392c00b03773653b4ad1ce66f6d0cacd6b3021cbdeee99a91',
 'smali_classes3/ucy.smali':'8efcf4301a6d8d16f5268bdef316c017086a68ba56c5e8ff0c6c68d4fec87b17',
 'smali_classes2/rup.smali':'8a6d43ebaaeb0ef5696bec5c8806a372e475a6b26a05f012c59a94df51c2ce02',
 'smali_classes2/iju.smali':'55a7014a4c61acd2be589357d4ec0bccfa785b724e1960cff021ba26643705bf',
 'smali_classes2/tfh.smali':'5ddf8dd3cf0cd88b044f61c820fa80d26f9556fc2b7f0b02bda1202b526391af',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def req(c,m):
    if not c: raise SystemExit('FAIL: '+m)
def method_span(t, signature):
    m=re.search(r'(?ms)^\.method[^\n]*'+re.escape(signature)+r'\n.*?^\.end method\n?',t)
    req(m is not None,'method missing '+signature); return m
for rel,h in EXPECTED.items():
    p=ROOT/rel; req(p.is_file(),'missing '+rel); req(sha(p)==h,f'input drift {rel}')
texts={p.relative_to(ROOT).as_posix():p.read_text(errors='replace') for p in ROOT.rglob('*.smali')}
uda_refs=sorted(k for k,v in texts.items() if 'Luda;' in v)
ucy_refs=sorted(k for k,v in texts.items() if 'Lucy;' in v)
req(uda_refs==sorted(['smali_classes3/uda.smali','smali_classes2/iju.smali','smali_classes2/rup.smali','smali_classes2/tfh.smali']), 'unexpected Luda graph')
req(ucy_refs==sorted(['smali_classes3/ucy.smali','smali_classes3/uda.smali','smali_classes2/iju.smali','smali_classes2/rup.smali']), 'unexpected Lucy graph')
all_join='\n'.join(texts.values())
req(all_join.count('Ltfh;-><init>(Ljava/lang/Object;I)V')==3,'unexpected tfh constructor count')
req(all_join.count('Lrup;-><init>(Luda;Lucx;Luen;I)V')==1,'unexpected dedicated rup ctor count')
selector19=[]
for k,v in texts.items():
    if 'Liju;-><init>(Ljava/lang/Object;Ljava/lang/Object;I)V' in v and re.search(r'const/16\s+v\d+,\s+0x13(?s:.{0,180})Liju;-><init>\(Ljava/lang/Object;Ljava/lang/Object;I\)V',v): selector19.append(k)
req(selector19==['smali_classes3/uda.smali'],'unexpected Iju selector19 producer')
# rup: delete dedicated ctor, reject default selector, remove unreachable network block
p=ROOT/'smali_classes2/rup.smali'; t=p.read_text(); m=method_span(t,'<init>(Luda;Lucx;Luen;I)V'); t=t[:m.start()]+t[m.end():]
m=re.search(r'(    packed-switch v0, :pswitch_data_0\n)(?s:.*?)(\n    :pswitch_0\n)',t); req(m is not None,'rup dispatch missing')
t=t[:m.start()]+m.group(1)+'\n    new-instance v0, Ljava/lang/UnsupportedOperationException;\n\n    const-string v2, "Removed Primes network reporter callback branch"\n\n    invoke-direct {v0, v2}, Ljava/lang/UnsupportedOperationException;-><init>(Ljava/lang/String;)V\n\n    throw v0\n'+m.group(2)+t[m.end():]
start=t.find('    :goto_3\n'); end=t.find('    :pswitch_data_0\n',start); req(start>=0 and end>start,'rup network block missing'); block=t[start:end]; req('Luda;' in block and 'Lucy;' in block and 'NetworkCapture.java' in block,'rup target mismatch'); t=t[:start]+t[end:]; p.write_text(t)
# iju selector19
p=ROOT/'smali_classes2/iju.smali'; t=p.read_text(); start=t.find('    :pswitch_0\n'); end=t.find('    :pswitch_1\n',start); req(start>=0 and end>start,'iju block missing'); req('Luda;' in t[start:end] and 'Lucy;' in t[start:end],'iju target mismatch'); repl='    :pswitch_0\n    new-instance v0, Ljava/lang/UnsupportedOperationException;\n\n    const-string v1, "Removed Primes network reporter aggregation branch"\n\n    invoke-direct {v0, v1}, Ljava/lang/UnsupportedOperationException;-><init>(Ljava/lang/String;)V\n\n    throw v0\n\n'; p.write_text(t[:start]+repl+t[end:])
# tfh default network branch
p=ROOT/'smali_classes2/tfh.smali'; t=p.read_text(); needle='    if-eq v0, v3, :cond_0\n'; start=t.find(needle); req(start>=0,'tfh condition missing'); start+=len(needle); end=t.find('    :cond_0\n',start); req(end>start and 'Luda;' in t[start:end],'tfh target mismatch'); repl='\n    new-instance v0, Ljava/lang/UnsupportedOperationException;\n\n    const-string v1, "Removed Primes network reporter retry branch"\n\n    invoke-direct {v0, v1}, Ljava/lang/UnsupportedOperationException;-><init>(Ljava/lang/String;)V\n\n    throw v0\n\n'; p.write_text(t[:start]+repl+t[end:])
(ROOT/'smali_classes3/uda.smali').unlink(); (ROOT/'smali_classes3/ucy.smali').unlink()
texts2={p.relative_to(ROOT).as_posix():p.read_text(errors='replace') for p in ROOT.rglob('*.smali')}; joined2='\n'.join(texts2.values())
for marker in ['Luda;','Lucy;','NetworkMetricServiceImpl','NetworkCapture.java']: req(marker not in joined2,'network reporter marker remains '+marker)
for marker in ['org.futo.voiceinput.moonshine','Lcom/mekromn/meboard/VoiceProviderRelayActivity;','Test Meboard']: req(marker in joined2,'locked feature missing '+marker)
for marker in ['Lrqw;','Lpsa;','Lpsp;','Lmck;','Lmcj;','Lkgd;','Lkgb;','Lkga;','Lkfu;','Lkfy;','Lkfw;','Lkfx;','Lkfv;']: req(marker not in joined2,'locked removal returned '+marker)
REPORT.write_text(json.dumps({'base_stage':49,'base_apk_sha256':BASE_APK_SHA,'deleted_classes':['uda','ucy'],'modified_classes':['rup','iju','tfh'],'removed_scope':'unconstructible Primes NetworkMetricServiceImpl + dedicated converter + dead shared callback branches','runtime_tested':False,'privacy_final':False},indent=2)+'\n')
print('PASS stage50 network reporter patch')
