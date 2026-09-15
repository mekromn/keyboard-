#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, sys
ROOT=Path(sys.argv[1]); REPORT=Path(sys.argv[2])
EXPECTED={
 'smali/kgm.smali':'89ef84cd2a6582e20b7851bf706e03f3dc0d923df7a797d07249a42c411b4995',
 'smali/gau.smali':'1e1edd8e7894eef6c47ce6f403b33970d93236ba0383611aa0379b1f2a7342fd',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
for rel,h in EXPECTED.items():
 p=ROOT/rel
 if sha(p)!=h: raise SystemExit(f'input drift {rel}: {sha(p)} != {h}')
p=ROOT/'smali/kgm.smali'; t=p.read_text()
old='''    :cond_4\n    iget-object p1, p0, Lkgm;->b:Landroid/content/Context;\n\n    .line 156\n    .line 157\n    invoke-static {p1}, Lkgd;->f(Landroid/content/Context;)V\n\n    .line 158\n    .line 159\n    .line 160\n    iget-object p1, p0, Lkgm;->e:Lkgy;'''
new='''    :cond_4\n    iget-object p1, p0, Lkgm;->e:Lkgy;'''
if t.count(old)!=1: raise SystemExit('kgm target block count != 1')
p.write_text(t.replace(old,new,1))
p=ROOT/'smali/gau.smali'; t=p.read_text()
old='''    :pswitch_4\n    iget-object p0, p0, Lgau;->a:Ljava/lang/Object;\n\n    .line 199\n    .line 200\n    check-cast p0, Lkje;\n\n    .line 201\n    .line 202\n    iget-object p0, p0, Lkje;->b:Landroid/content/Context;\n\n    .line 203\n    .line 204\n    invoke-static {p0}, Lkgd;->i(Landroid/content/Context;)V\n\n    .line 205\n    .line 206\n    .line 207\n    return-void'''
new='''    :pswitch_4\n    return-void'''
if t.count(old)!=1: raise SystemExit('gau target block count != 1')
p.write_text(t.replace(old,new,1))
alltxt='\n'.join(x.read_text(errors='replace') for x in ROOT.glob('smali*/**/*.smali'))
if 'Lkgd;->f(Landroid/content/Context;)V' in alltxt: raise SystemExit('kgd.f trigger remains')
for q in ROOT.glob('smali*/**/*.smali'):
 s=q.read_text(errors='replace')
 if 'Lkgd;->i(Landroid/content/Context;)V' in s and q.name!='kgd.smali': raise SystemExit(f'external kgd.i remains in {q}')
for bad in ['Lrqw;','VoiceDonationManager','maybeAddDonationRequest','Lpsa;','Lpsp;','Lmck;','Lmcj;']:
 if bad in alltxt: raise SystemExit('locked removal returned '+bad)
if 'org.futo.voiceinput.moonshine' not in alltxt: raise SystemExit('moonshine target missing')
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps({'base':'stage46','changed':['smali/kgm.smali','smali/gau.smali'],'removed_live_triggers':['kgm.f -> kgd.f(context)','gau selector15 -> kgd.i(context)'],'dedicated_donation_cluster_deleted':False,'next':'delete unreachable static donation dialog/banner cluster after runtime pass'},indent=2)+'\n')
print('PASS stage47 patch')
