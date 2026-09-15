#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,json,argparse

EXPECTED={
'smali/psa.smali':'9e1945b4122914c6c7171f4b9cad8ab43781bdf967ae635115b745757373dd01',
'smali/psp.smali':'d57032d8080e0d645653658d4a7658d88f758d588a2e41d041e1288193e6ba33',
'smali/mck.smali':'d21f743c0f4b0c13fdc1295738562c110f06624fe1635c6561594fc03a26a386',
'smali/mcj.smali':'d4b6b7e74cc289d65dd9e589d21521947f6dce8e88698725568c1376eb8b8f54',
'smali/msp.smali':'8e56e4169563c04e463b9260c06001434b2c9432af43fe81219daecc5bbf7a42',
'smali/fol.smali':'252901639ccda47bd5e5089801993f38727b18d5de7fb4c5d72ea7e702c5fae9',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def req(ok,msg):
    if not ok: raise SystemExit('FAIL: '+msg)
ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); args=ap.parse_args(); ROOT=args.root.resolve()
for rel,h in EXPECTED.items(): req(sha(ROOT/rel)==h,'input drift '+rel)
files={p.relative_to(ROOT).as_posix():p.read_text(errors='replace') for p in ROOT.glob('smali*/**/*.smali')}
for desc,allowed in {
    'Lpsa;':{'smali/psa.smali','smali/msp.smali'},
    'Lpsp;':{'smali/psp.smali','smali/fol.smali','smali/mck.smali'},
    'Lmck;':{'smali/mck.smali'},
    'Lmcj;':{'smali/mcj.smali','smali/mck.smali'},
}.items():
    refs={p for p,t in files.items() if desc in t}
    req(refs<=allowed, f'unexpected ingress {desc}: {sorted(refs-allowed)}')
p=ROOT/'smali/msp.smali'; t=p.read_text()
block='''    new-instance v9, Lpsa;\n\n    invoke-direct {v9, v6}, Lpsa;-><init>(Lqhy;)V\n\n    iput-object v9, v0, Lpsb;->l:Ljava/util/function/Supplier;\n\n'''
req(t.count(block)==1,'msp psa install block not unique')
t=t.replace(block,'',1); p.write_text(t)
p=ROOT/'smali/fol.smali'; t=p.read_text()
m=re.search(r'(?ms)^\.method public final fV\(Lqhy;Ljava/lang/String;\)V\n.*?^\.end method\n?',t)
req(m is not None,'fol fV missing'); b=m.group(0)
b2,n=re.subn(r'(?ms)^    :pswitch_0\n.*?(?=^    :pswitch_1\n)','',b,count=1)
req(n==1,'fol psp branch removal count')
old='''    .line 421\n    :pswitch_data_0\n    .packed-switch 0x0\n        :pswitch_e\n        :pswitch_d\n        :pswitch_d\n        :pswitch_c\n        :pswitch_b\n        :pswitch_a\n        :pswitch_9\n        :pswitch_8\n        :pswitch_8\n        :pswitch_7\n        :pswitch_6\n        :pswitch_5\n        :pswitch_4\n        :pswitch_3\n        :pswitch_2\n        :pswitch_1\n        :pswitch_0\n    .end packed-switch\n'''
new='''    .line 421\n    :pswitch_data_0\n    .sparse-switch\n        0x0 -> :pswitch_e\n        0x1 -> :pswitch_d\n        0x2 -> :pswitch_d\n        0x3 -> :pswitch_c\n        0x4 -> :pswitch_b\n        0x5 -> :pswitch_a\n        0x6 -> :pswitch_9\n        0x7 -> :pswitch_8\n        0x8 -> :pswitch_8\n        0x9 -> :pswitch_7\n        0xa -> :pswitch_6\n        0xb -> :pswitch_5\n        0xc -> :pswitch_4\n        0xd -> :pswitch_3\n        0xe -> :pswitch_2\n        0xf -> :pswitch_1\n    .end sparse-switch\n'''
req(old in b2,'fol expected switch table missing')
b2=b2.replace('    packed-switch v0, :pswitch_data_0','    sparse-switch v0, :pswitch_data_0',1).replace(old,new,1)
t=t[:m.start()]+b2+t[m.end():]; p.write_text(t)
for rel in ['smali/psa.smali','smali/psp.smali','smali/mck.smali','smali/mcj.smali']:
    (ROOT/rel).unlink()
after={p.relative_to(ROOT).as_posix():p.read_text(errors='replace') for p in ROOT.glob('smali*/**/*.smali')}
joined='\n'.join(after.values())
for desc in ['Lpsa;','Lpsp;','Lmck;','Lmcj;']:
    req(desc not in joined,'residual descriptor '+desc)
for marker in ['UserMetricsPreferencesCollectionBasisResolver','CollectionBasisResolverHolder{conditions=','CollectionBasisResolverConditions{accountNames=']:
    req(marker not in joined,'residual removed marker '+marker)
req('new-instance v1, Lewh;' in after['smali/psb.smali'] and 'const/16 v3, 0x13' in after['smali/psb.smali'], 'stock default false supplier not preserved')
for bad in ['Lrqw;','VoiceDonationManager','maybeAddDonationRequest','PrivacySettingsFragment;->aD(Z)V']:
    req(bad not in joined,'locked removal regressed '+bad)
relay=after['smali/com/mekromn/meboard/VoiceProviderRelayActivity.smali']
req('org.futo.voiceinput.moonshine' in relay,'Moonshine direct target missing')
req('smali/com/mekromn/meboard/VoiceResultCommitRunnable.smali' in after,'deferred commit runnable missing')
req('commitText' in after['smali/com/mekromn/meboard/VoiceProviderChooser.smali'],'deferred commit path missing')
report={
 'stage':'44', 'base':'Stage43 cumulative working baseline',
 'deleted_classes':['psa','psp','mck','mcj'],
 'modified_classes':['msp','fol'],
 'purpose':'remove user-metrics preference permission bridge and orphan UserMetrics collection-basis resolver cluster',
 'locked_stage28_removals_preserved':True,'moonshine_stage42_behavior_preserved':True,
 'privacy_final':False,'runtime_tested':False,
}
(ROOT/'stage44_patch_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
