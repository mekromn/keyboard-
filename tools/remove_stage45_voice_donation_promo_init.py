#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, argparse

EXPECTED={
 'smali/kgm.smali':'170da03316ae5281ed3111cd7e369bbfeaffef0a437233ce40841fd720811cdc',
 'smali/com/google/android/apps/inputmethod/libs/nga/impl/input/NgaInputManager.smali':'896a71d1ad20c69413999ca3c895bc1824599c9321077110da80fc68fe012e47',
}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def req(x,msg):
    if not x: raise SystemExit('FAIL: '+msg)

def cut_between(text,start,end,name):
    req(text.count(start)==1, name+' start count')
    a=text.index(start)
    b=text.index(end,a)
    req(b>a,name+' end ordering')
    return text[:a]+text[b:]

ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); a=ap.parse_args(); root=a.root
for rel,h in EXPECTED.items(): req(sha(root/rel)==h,'input drift '+rel)

p=root/'smali/kgm.smali'; t=p.read_text()
t=cut_between(t,'    sget-object v2, Lkim;->d:Lkim;\n\n','    :cond_1b\n','kgm donation init')
p.write_text(t)

p=root/'smali/com/google/android/apps/inputmethod/libs/nga/impl/input/NgaInputManager.smali'; t=p.read_text()
t=cut_between(t,'    sget-object v3, Lkml;->e:Lkml;\n\n','    :cond_b\n','NgaInputManager donation init')
p.write_text(t)

files={p.relative_to(root).as_posix():p.read_text(errors='replace') for p in root.glob('smali*/**/*.smali')}
joined='\n'.join(files.values())
req('new-instance p0, Lkgd;' not in joined and 'new-instance v2, Lkgd;' not in joined,'VoiceDonationPromoManager construction remains')
req('invoke-direct {p0, p1, v2}, Lkgd;-><init>' not in joined,'standard kgd constructor remains')
req('invoke-direct {v2, v0, v1}, Lkgd;-><init>' not in joined,'NGA kgd constructor remains')
req('maybeInitializeVoiceDonationPromoManager' not in files['smali/kgm.smali'],'standard init marker remains')
req('maybeInitializeVoiceDonationPromoManager' not in files['smali/com/google/android/apps/inputmethod/libs/nga/impl/input/NgaInputManager.smali'],'NGA init marker remains')
req('iput-object v9, v3, Lkgw;->u:Lkgd;' in files['smali/kgm.smali'],'standard null reset removed')
req('iput-object v3, p0, Lcom/google/android/apps/inputmethod/libs/nga/impl/input/NgaInputManager;->l:Lkgd;' in files['smali/com/google/android/apps/inputmethod/libs/nga/impl/input/NgaInputManager.smali'],'NGA null reset removed')
for bad in ['Lrqw;','VoiceDonationManager','maybeAddDonationRequest','PrivacySettingsFragment;->aD(Z)V','Lpsa;','Lpsp;','Lmck;','Lmcj;']:
    req(bad not in joined,'locked removal regressed '+bad)
relay=files['smali/com/mekromn/meboard/VoiceProviderRelayActivity.smali']
req('org.futo.voiceinput.moonshine' in relay,'Moonshine direct target missing')
req('smali/com/mekromn/meboard/VoiceResultCommitRunnable.smali' in files,'deferred result helper missing')
req('commitText' in files['smali/com/mekromn/meboard/VoiceProviderChooser.smali'],'deferred commit path missing')

report={
 'stage':'45',
 'base_sha256':'347127345444ba672e6335226984dddaf20262350b5c31cac347af18f17d14fe',
 'scope':'remove all live VoiceDonationPromoManager construction/initialization blocks',
 'modified_classes':['kgm','com.google.android.apps.inputmethod.libs.nga.impl.input.NgaInputManager'],
 'deleted_classes':[],
 'kgd_construction_sites_remaining':0,
 'kgd_fields_retained_and_nulled':True,
 'locked_stage28_stage44_removals_preserved':True,
 'moonshine_stage42_behavior_preserved':True,
 'privacy_final':False,
 'runtime_tested':False,
}
(root/'stage45_patch_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
