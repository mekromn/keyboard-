#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,json,sys
ROOT=Path(sys.argv[1]); REPORT=Path(sys.argv[2])
EXPECTED={
 'tzq.smali':'db94fec3233c43bcada5830f1a0736fb92b36cae3d386c6fa6c176927b30fee0',
 'twk.smali':'90b6101024ef38d13eeacb22bf2cdfc71020794654069801498ca2534d73bca5',
}
BASE_SHA='026b7a1961d515e37a38ae609ac4dc2be00c46d44cea0a4fa9179fe6e0c5497f'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def req(c,m):
    if not c: raise SystemExit(m)
for name,h in EXPECTED.items():
    p=ROOT/name; req(p.is_file(), 'missing '+name); req(sha(p)==h, f'input drift {name}: {sha(p)} != {h}')
allfiles=list(ROOT.rglob('*.smali'))
texts={p.relative_to(ROOT).as_posix():p.read_text(errors='replace') for p in allfiles}
refs=[n for n,t in texts.items() if n!='twk.smali' and 'Ltwk;' in t]
req(refs==[], 'Ltwk has surviving inbound refs: '+repr(refs))
joined='\n'.join(texts.values())
req(joined.count('Ltzq;-><init>')==1, f'unexpected tzq constructor call count {joined.count("Ltzq;-><init>")}')
eoi=texts.get('eoi.smali','')
pat=r'new-instance v14, Ltzq;(?s:.*?)const/16 v24, 0x1(?s:.*?)invoke-direct/range \{v14 \.\. v25\}, Ltzq;-><init>\(Laals;Laals;Laals;Laals;Laals;Laals;Laals;Laals;Laals;I\[B\)V'
req(re.search(pat,eoi) is not None, 'tzq typed construction is not the expected selector-1 [B] site')
p=ROOT/'tzq.smali'; t=p.read_text()
pat=r'(    if-eq v0, v1, :cond_0\n)(?s:.*?)(\n    :cond_0\n)'
m=re.search(pat,t); req(m is not None, 'tzq default branch not found')
old=m.group(0)
req('new-instance v3, Luda;' in old and 'Luda;-><init>' in old, 'tzq default branch does not contain network reporter construction')
replacement=m.group(1)+'''\n    new-instance v0, Ljava/lang/UnsupportedOperationException;\n\n    const-string v1, "Removed Primes network metric provider branch"\n\n    invoke-direct {v0, v1}, Ljava/lang/UnsupportedOperationException;-><init>(Ljava/lang/String;)V\n\n    throw v0\n'''+m.group(2)
t=t[:m.start()]+replacement+t[m.end():]; p.write_text(t)
(ROOT/'twk.smali').unlink()
texts2={p.relative_to(ROOT).as_posix():p.read_text(errors='replace') for p in ROOT.rglob('*.smali')}
joined2='\n'.join(texts2.values())
req('Ltwk;' not in joined2, 'twk descriptor remains')
req('new-instance v3, Luda;' not in texts2['tzq.smali'], 'Luda construction remains in tzq')
req('Luda;-><init>' not in texts2['tzq.smali'], 'Luda ctor call remains in tzq')
for marker in ['org.futo.voiceinput.moonshine','Lcom/mekromn/meboard/VoiceProviderRelayActivity;']:
    req(marker in joined2, 'missing locked feature marker '+marker)
for marker in ['Lpsa;','Lpsp;','Lmck;','Lmcj;']:
    req(marker not in joined2, 'locked removal returned '+marker)
REPORT.write_text(json.dumps({
 'base_stage':48,'base_sha256':BASE_SHA,
 'deleted_classes':['twk'],'modified_classes':['tzq'],
 'removed_path':'unreachable tzq default branch constructing Primes NetworkMetricServiceImpl (Luda)',
 'typed_tzq_construction':'one selector-1 [B] site in eoi; network/default selector has no typed producer',
 'runtime_tested':False,'privacy_final':False
},indent=2)+'\n')
print('PASS stage49 patch')
