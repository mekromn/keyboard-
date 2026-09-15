#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, json, argparse, shutil

EXPECTED = {
 'smali/kgm.smali':'ee54009a523f187fce2617e87d6e3441657725bf9f611baaabf2a6803327445e',
 'smali/kgw.smali':'0b5c02bdd37ec3ca138f069a3012dc2896b76a08cd2f12745a1540e2aeb9afdf',
 'smali/com/google/android/apps/inputmethod/libs/nga/impl/input/NgaInputManager.smali':'5244b8a493f02df1b36c7fcaa4eca139dd0336010c99aa1bec7e4c1dc59126d8',
 'smali_classes2/kgv.smali':'c53a7d2b7e241c7b590c59073bf276a02beb86c4c11ce12159eb1a8c09569934',
 'smali_classes2/ihv.smali':'1ac9923eee37ebc29b9c17136cd0ffa1e5140d927c92e2e82bd3d86e8463549d',
}
BASE_SHA='0eb4edc0f15917bdafdc32dafdbe3a1d9078f6a7dbf9dbd4fe30eb45f2dda3a2'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def req(x,msg):
    if not x: raise SystemExit('FAIL: '+msg)

def remove_method(t, signature, name):
    m=re.search(r'(?ms)^\.method[^\n]*'+re.escape(signature)+r'\n.*?^\.end method\n?',t)
    req(m is not None, 'missing method '+name)
    return t[:m.start()]+t[m.end():]

def sub_exact(t, old, new, name):
    req(t.count(old)==1, f'{name}: exact block count={t.count(old)}')
    return t.replace(old,new,1)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('--backup',type=Path); a=ap.parse_args(); root=a.root
    for rel,h in EXPECTED.items():
        p=root/rel; req(p.is_file(),'missing '+rel); req(sha(p)==h,'input drift '+rel)
    if a.backup:
        a.backup.mkdir(parents=True,exist_ok=True)
        for rel in EXPECTED:
            dest=a.backup/rel; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(root/rel,dest)

    # kgm: remove donation-only helper and both calls; remove stale null write to kgw.u.
    p=root/'smali/kgm.smali'; t=p.read_text()
    t=remove_method(t,'l()V','kgm.l')
    req(t.count('    invoke-direct {p0}, Lkgm;->l()V\n')==2,'kgm.l call count')
    t=t.replace('    invoke-direct {p0}, Lkgm;->l()V\n','',2)
    req(t.count('    iput-object v9, v3, Lkgw;->u:Lkgd;\n')==1,'kgm kgw.u null write count')
    t=t.replace('    iput-object v9, v3, Lkgw;->u:Lkgd;\n','',1)
    p.write_text(t)

    # kgw: remove field + donation-only cleanup helper; drop call on inactive path and stopVoiceInput donation tail.
    p=root/'smali/kgw.smali'; t=p.read_text()
    req(t.count('.field public u:Lkgd;\n')==1,'kgw.u field count')
    t=t.replace('.field public u:Lkgd;\n','',1)
    t=remove_method(t,'j()V','kgw.j')
    req(t.count('    invoke-virtual {p0}, Lkgw;->j()V\n')==1,'kgw.j call count')
    t=t.replace('    invoke-virtual {p0}, Lkgw;->j()V\n','',1)
    old='''    iget-object v1, p0, Lkgw;->u:Lkgd;\n\n    .line 56\n    .line 57\n    if-eqz v1, :cond_1\n\n    .line 58\n    .line 59\n    invoke-virtual {v1}, Lkgd;->h()V\n\n    .line 60\n    .line 61\n    .line 62\n    :cond_1\n'''
    t=sub_exact(t,old,'','kgw.r donation tail')
    p.write_text(t)

    # NGA manager: keep all non-donation lifecycle behavior, remove only stale field and field-specific branches.
    p=root/'smali/com/google/android/apps/inputmethod/libs/nga/impl/input/NgaInputManager.smali'; t=p.read_text()
    req(t.count('.field public l:Lkgd;\n')==1,'NGA l field count')
    t=t.replace('.field public l:Lkgd;\n','',1)
    old='''    iget-object p0, p0, Lcom/google/android/apps/inputmethod/libs/nga/impl/input/NgaInputManager;->l:Lkgd;\n\n    .line 113\n    .line 114\n    if-eqz p0, :cond_4\n\n    .line 115\n    .line 116\n    invoke-virtual {p0}, Lkgd;->h()V\n\n    .line 117\n    .line 118\n    .line 119\n    :cond_4\n'''
    t=sub_exact(t,old,'','NGA.s donation tail')
    old='''    iget-object v0, p0, Lcom/google/android/apps/inputmethod/libs/nga/impl/input/NgaInputManager;->l:Lkgd;\n\n    .line 5\n    .line 6\n    const/4 v1, 0x0\n\n    .line 7\n    if-eqz v0, :cond_0\n\n    .line 8\n    .line 9\n    iput-object v1, p0, Lcom/google/android/apps/inputmethod/libs/nga/impl/input/NgaInputManager;->l:Lkgd;\n\n    .line 10\n    .line 11\n    :cond_0\n'''
    # preserve v1=null because the next Handler and gwc calls use it.
    t=sub_exact(t,old,'    const/4 v1, 0x0\n\n','NGA.c donation field clear')
    req(t.count('    iput-object v3, p0, Lcom/google/android/apps/inputmethod/libs/nga/impl/input/NgaInputManager;->l:Lkgd;\n')==1,'NGA.o null write count')
    t=t.replace('    iput-object v3, p0, Lcom/google/android/apps/inputmethod/libs/nga/impl/input/NgaInputManager;->l:Lkgd;\n','',1)
    p.write_text(t)

    # kgv: remove result/lifecycle hook into the impossible kgw.u instance.
    p=root/'smali_classes2/kgv.smali'; t=p.read_text()
    old='''    iget-object v1, v0, Lkgw;->u:Lkgd;\n\n    .line 20\n    .line 21\n    if-eqz v1, :cond_1\n\n    .line 22\n    .line 23\n    invoke-virtual {v1}, Lkgd;->j()V\n\n    .line 24\n    .line 25\n    .line 26\n    :cond_1\n'''
    t=sub_exact(t,old,'','kgv donation lifecycle hook')
    p.write_text(t)

    # ihv: remove NGA synthetic lifecycle hook; preserve the following non-donation a() call.
    p=root/'smali_classes2/ihv.smali'; t=p.read_text()
    old='''    iget-object v1, v4, Lcom/google/android/apps/inputmethod/libs/nga/impl/input/NgaInputManager;->l:Lkgd;\n\n    .line 1142\n    .line 1143\n    if-eqz v1, :cond_22\n\n    .line 1144\n    .line 1145\n    invoke-virtual {v1}, Lkgd;->j()V\n\n    .line 1146\n    .line 1147\n    .line 1148\n    :cond_22\n'''
    t=sub_exact(t,old,'','ihv NGA donation lifecycle hook')
    p.write_text(t)

    files={p.relative_to(root).as_posix():p.read_text(errors='replace') for p in root.glob('smali*/**/*.smali')}
    joined='\n'.join(files.values())
    for bad in ['Lkgw;->u:Lkgd;','NgaInputManager;->l:Lkgd;','Lkgm;->l()V','Lkgw;->j()V']:
        req(bad not in joined,'stale donation instance plumbing remains '+bad)
    # prior locked removals
    for bad in ['Lrqw;','VoiceDonationManager','maybeAddDonationRequest','PrivacySettingsFragment;->aD(Z)V','Lpsa;','Lpsp;','Lmck;','Lmcj;']:
        req(bad not in joined,'locked removal regressed '+bad)
    relay=files['smali/com/mekromn/meboard/VoiceProviderRelayActivity.smali']
    req('org.futo.voiceinput.moonshine' in relay,'Moonshine direct target missing')
    req('smali/com/mekromn/meboard/VoiceResultCommitRunnable.smali' in files,'deferred result helper missing')
    report={
      'stage':'46','base_sha256':BASE_SHA,
      'scope':'remove unreachable VoiceDonationPromoManager instance fields and lifecycle plumbing after Stage45 constructor removal',
      'modified_classes':['kgm','kgw','com.google.android.apps.inputmethod.libs.nga.impl.input.NgaInputManager','kgv','ihv'],
      'deleted_fields':['kgw.u:Lkgd','NgaInputManager.l:Lkgd'],
      'deleted_methods':['kgm.l()V','kgw.j()V'],
      'static_donation_code_intentionally_retained':True,
      'locked_removals_preserved':True,'moonshine_preserved':True,
      'privacy_final':False,'runtime_tested':False,
    }
    (root/'stage46_patch_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
