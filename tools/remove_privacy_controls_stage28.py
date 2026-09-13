#!/usr/bin/env python3
"""Stage-27 -> Stage-28 physical privacy-control and donation-sink removal.

Scope of this guarded pass:
- remove Share usage statistics, Improve for everyone, and Audio donations rows;
- remove the two matching managed-configuration restrictions;
- remove privacy-screen audio-donation setup/callback cases;
- physically delete VoiceDonationManager and both request-builder call paths.

This does NOT claim all usage-metrics/federated/promo code is gone. Local
personalization, learned-data deletion, ordinary dictation, recognizers, local
AI and retained feature networking are intentionally preserved.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

INPUT_SHA='1827fc3a917f28d466f6572e3967acd669f5836df1e8cb2d432adb58c3d66841'
EXPECTED={
 'res/xml/setting_privacy.xml':'e4792fac80756af641e9ebd476cbaa2eb0ebe8db5818d2dee17fd852a5604a45',
 'res/xml/APKTOOL_RENAMED_0x7f170002.xml':'753d535987519cfb7b5d3cf38f90fdf7baab0d4b47d25117c063be3938743127',
 'smali_classes2/com/google/android/apps/inputmethod/latin/preference/PrivacySettingsFragment.smali':'0a6fd109f54dc2db376486f8b4133cb735420be2ef2978a7d8a9d21ca9fd8058',
 'smali_classes2/eke.smali':'997a00b84968ffbf976d8c5206f6a73867cb0b7dcee78953b4c147ffd0895a61',
 'smali_classes2/kjr.smali':'d4ad2fc4870f40b9836431ff63e5a00d8fe78c3223ac1db77a6abbc6c2637d96',
 'smali_classes2/kjo.smali':'2d4342567e93a1b3ac255a7e6c2628f56c1bd654bbc282105b8618b3088c4788',
 'smali_classes2/smc.smali':'fe077a55f40119550f666601a7f168d533ac76b1a79065b783731d4c92bbe7e5',
 'smali_classes2/rqw.smali':'f42381d0d2e1171d3d46c3fe3ea20c0aef629b7d44f4d810c9d2d5110f2387f2',
}
METHOD=re.compile(r'(?ms)^\.method[^\n]*\n.*?^\.end method\n?')

def require(ok,msg):
    if not ok: raise ValueError(msg)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def method(text,sig):
    m=re.search(r'(?ms)^\.method[^\n]*'+re.escape(sig)+r'\n.*?^\.end method\n?',text,re.M)
    if not m: raise ValueError('missing method '+sig)
    return m
def sub1(text,pat,repl,name):
    out,n=re.subn(pat,repl,text,count=1,flags=re.M|re.S)
    require(n==1,f'{name}: replacement count {n}')
    return out

def apply(root:Path,report:Path,dry_run=False):
    for rel,h in EXPECTED.items():
        p=root/rel; require(p.is_file(),'missing '+rel); require(sha(p)==h,'input drift '+rel)
    before={rel:(root/rel).read_bytes() for rel in EXPECTED}

    p=root/'res/xml/setting_privacy.xml'; t=p.read_text()
    for key in ['@string/APKTOOL_RENAMED_0x7f140a2d','@string/APKTOOL_RENAMED_0x7f140b93','@string/APKTOOL_RENAMED_0x7f140a2f']:
        old=t
        t=re.sub(r'^\s*<[^>]+android:key="'+re.escape(key)+r'"[^>]*/>\s*\n?','',t,flags=re.M)
        require(t!=old,'privacy row not found '+key)
    t=re.sub(r'\s*<androidx\.preference\.PreferenceCategory android:title="@string/APKTOOL_RENAMED_0x7f140d4b" android:key="@string/APKTOOL_RENAMED_0x7f140d4a">\s*</androidx\.preference\.PreferenceCategory>\s*','\n',t,flags=re.S)
    if not dry_run:p.write_text(t)

    p=root/'res/xml/APKTOOL_RENAMED_0x7f170002.xml'; t=p.read_text()
    for key in ['enable_user_metrics','user_enable_federated_training']:
        old=t;t=re.sub(r'^\s*<restriction\b[^>]*android:key="'+key+r'"[^>]*/>\s*\n?','',t,flags=re.M)
        require(t!=old,'managed restriction not found '+key)
    if not dry_run:p.write_text(t)

    p=root/'smali_classes2/com/google/android/apps/inputmethod/latin/preference/PrivacySettingsFragment.smali'; t=p.read_text()
    m=method(t,'ac()V')
    repl='''.method public final ac()V\n    .locals 0\n\n    invoke-super {p0}, Lcom/google/android/apps/inputmethod/latin/preference/dictionary/AbstractDictionarySettingsFragment;->ac()V\n\n    return-void\n.end method\n'''
    t=t[:m.start()]+repl+t[m.end():]
    m=method(t,'aD(Z)V');t=t[:m.start()]+t[m.end():]
    if not dry_run:p.write_text(t)

    p=root/'smali_classes2/eke.smali';t=p.read_text();m=method(t,'run()V');b=m.group(0)
    a=b.index('    :pswitch_0\n');z=b.index('    :pswitch_2\n');b=b[:a]+b[z:]
    tm=re.search(r'(?ms)    :pswitch_data_0\n    \.packed-switch 0x0\n(.*?)    \.end packed-switch',b);require(tm is not None,'eke table')
    labels=[x.strip() for x in tm.group(1).splitlines() if x.strip()];require(len(labels)==20,'eke selector count')
    new='    :pswitch_data_0\n    .sparse-switch\n'+''.join(f'        0x{i:x} -> {lab}\n' for i,lab in enumerate(labels[:18]))+'    .end sparse-switch'
    b=b[:tm.start()]+new+b[tm.end():];b=b.replace('    packed-switch v0, :pswitch_data_0','    sparse-switch v0, :pswitch_data_0',1)
    t=t[:m.start()]+b+t[m.end():]
    if not dry_run:p.write_text(t)

    p=root/'smali_classes2/kjr.smali';t=p.read_text();t,n=re.subn(r'^\.field public final k:Lrqw;\n\n?','',t,count=1,flags=re.M);require(n==1,'kjr field')
    m=method(t,'<init>(Landroid/content/Context;Lkit;)V');b=sub1(m.group(0),r'\n\s*new-instance p2, Lrqw;.*?iput-object p2, p0, Lkjr;->k:Lrqw;\n','\n','kjr donation manager');t=t[:m.start()]+b+t[m.end():]
    if not dry_run:p.write_text(t)

    p=root/'smali_classes2/kjo.smali';t=p.read_text();m=method(t,'a(Lztc;)V');b=m.group(0)
    pos=b.index('    invoke-static {v2}, Lkkl;->m(Landroid/content/Context;)Z');a=b.rfind('    iget-object v2, v6, Lkjr;->i:Landroid/content/Context;',0,pos);require(a>=0,'kjo donation start')
    z=b.index('    invoke-virtual {v0, v1, v9, v2}, Lrqw;->a(Lztc;ZI)V',pos)+len('    invoke-virtual {v0, v1, v9, v2}, Lrqw;->a(Lztc;ZI)V')
    require('.catch' not in b[a:z],'kjo donation block has catch');b=b[:a]+b[z:];t=t[:m.start()]+b+t[m.end():]
    if not dry_run:p.write_text(t)

    p=root/'smali_classes2/smc.smali';t=p.read_text();t,n=re.subn(r'^\.field private final j:Lrqw;\n\n?','',t,count=1,flags=re.M);require(n==1,'smc field')
    m=method(t,'<init>(Landroid/content/Context;Lenf;Ljava/util/Locale;Lsal;Laabh;Labsf;Llcw;Lslw;)V');b=sub1(m.group(0),r'\n\s*new-instance p2, Lrqw;.*?iput-object p2, p0, Lsmc;->j:Lrqw;\n','\n','smc manager');t=t[:m.start()]+b+t[m.end():]
    m=method(t,'b(Ljava/lang/Long;Lablu;)Ljava/lang/Object;');b=m.group(0);a=b.index('    iget-object v2, v0, Lsmc;->j:Lrqw;');z=b.index('    invoke-virtual {v2, v1, v3, v0}, Lrqw;->a(Lztc;ZI)V',a)+len('    invoke-virtual {v2, v1, v3, v0}, Lrqw;->a(Lztc;ZI)V');require('.catch' not in b[a:z],'smc donation block has catch');b=b[:a]+b[z:];t=t[:m.start()]+b+t[m.end():]
    if not dry_run:p.write_text(t)

    if not dry_run:(root/'smali_classes2/rqw.smali').unlink()

    # End-state gates.
    texts='\n'.join(x.read_text(errors='replace') for x in root.glob('smali*/**/*.smali')) if not dry_run else ''
    if not dry_run:
        for bad in ['Lrqw;','VoiceDonationManager','maybeAddDonationRequest','PrivacySettingsFragment;->aD(Z)V']:
            require(bad not in texts,'residual '+bad)
        priv=(root/'res/xml/setting_privacy.xml').read_text();managed=(root/'res/xml/APKTOOL_RENAMED_0x7f170002.xml').read_text()
        require(all(x not in priv for x in ['0x7f140a2d','0x7f140b93','0x7f140a2f']),'removed row remains')
        require(all(x in priv for x in ['0x7f140b2a','0x7f140d95']),'retained local controls missing')
        require(all(x not in managed for x in ['enable_user_metrics','user_enable_federated_training']),'managed restriction remains')

    result={'input_apk_sha256':INPUT_SHA,'scope':'privacy rows + managed restrictions + direct audio donation request sink',
      'deleted_classes':['rqw'],'modified_classes':['PrivacySettingsFragment','eke','kjr','kjo','smc'],
      'modified_resources':['setting_privacy.xml','APKTOOL_RENAMED_0x7f170002.xml'],
      'retained_controls':['pref_key_use_personalized_dicts','setting_sync_clear_key'],
      'not_claimed_removed':['all usage-metrics backend code','all federated/training remnants','all voice-donation promo/preference helpers'],
      'runtime_tested':False,'privacy_final':False,'dry_run':dry_run}
    report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(result,indent=2)+'\n');return result

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--report',type=Path,required=True);p.add_argument('--dry-run',action='store_true');a=p.parse_args();print(json.dumps(apply(a.root,a.report,a.dry_run),indent=2))
if __name__=='__main__':main()
