#!/usr/bin/env python3
"""Verify Stage-28 settings/resource removal and direct donation-sink excision.

This intentionally does not certify all metrics/federated/donation-promo code as
removed. It independently checks the bounded Stage-28 claims and retained local
privacy controls. Input/output are Apktool decoded trees.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
TARGET_CHANGED={
 'smali_classes2/com/google/android/apps/inputmethod/latin/preference/PrivacySettingsFragment.smali',
 'smali_classes2/eke.smali','smali_classes2/kjr.smali','smali_classes2/kjo.smali','smali_classes2/smc.smali',
 'res/xml/setting_privacy.xml','res/xml/APKTOOL_RENAMED_0x7f170002.xml'
}
DELETED={'smali_classes2/rqw.smali'}
VOICE=['kgm','kgw','kht','kjp','kjm','kig','fct','ruo','rrf']
def check(x,m):
    if not x:raise ValueError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unique(root,cls):
    h=list(root.glob(f'smali*/**/{cls}.smali'));check(len(h)==1,f'{cls}: expected one class');return h[0]
def verify(before:Path,after:Path):
    bf={p.relative_to(before).as_posix():p for p in before.rglob('*') if p.is_file() and p.relative_to(before).parts[0]!='build'}
    af={p.relative_to(after).as_posix():p for p in after.rglob('*') if p.is_file() and p.relative_to(after).parts[0]!='build'}
    deleted=set(bf)-set(af); added=set(af)-set(bf); changed={p for p in set(bf)&set(af) if bf[p].read_bytes()!=af[p].read_bytes()}
    check(deleted==DELETED,'unexpected deleted decoded files: '+repr(deleted));check(not added,'decoded files added')
    check(changed==TARGET_CHANGED,'unexpected decoded changes: '+repr(changed))
    priv=(after/'res/xml/setting_privacy.xml').read_text();managed=(after/'res/xml/APKTOOL_RENAMED_0x7f170002.xml').read_text()
    check(all(x not in priv for x in ['0x7f140a2d','0x7f140b93','0x7f140a2f']),'removed privacy row remains')
    check(all(x in priv for x in ['0x7f140b2a','0x7f140d95']),'retained local privacy control missing')
    check(all(x not in managed for x in ['enable_user_metrics','user_enable_federated_training']),'managed setting remains')
    text='\n'.join(p.read_text(errors='replace') for p in after.glob('smali*/**/*.smali'))
    for marker in ['Lrqw;','VoiceDonationManager','maybeAddDonationRequest','PrivacySettingsFragment;->aD(Z)V']:
        check(marker not in text,'donation sink marker remains: '+marker)
    # Donation settings setup must no longer be in PrivacySettingsFragment.
    frag=unique(after,'PrivacySettingsFragment').read_text();check('setupVoiceDonationPref' not in frag and '0x7f140a2f' not in frag,'donation preference setup remains')
    voice={}
    for cls in VOICE:
        b=unique(before,cls);a=unique(after,cls);check(b.read_bytes()==a.read_bytes(),'core voice class changed: '+cls);voice[cls]=sha(a)
    check((before/'res/values/public.xml').read_bytes()==(after/'res/values/public.xml').read_bytes(),'public resource IDs changed')
    check((before/'AndroidManifest.xml').read_bytes()==(after/'AndroidManifest.xml').read_bytes(),'manifest changed')
    return {'passed':True,'deleted_class':'rqw (VoiceDonationManager)','changed_class_files':sorted(p for p in changed if p.endswith('.smali')),
      'changed_resource_files':sorted(p for p in changed if not p.endswith('.smali')),'core_voice_files_byte_identical':voice,
      'privacy_rows_removed':['enable_user_metrics','user_enable_federated_training','enable_voice_donation'],
      'retained_controls':['pref_key_use_personalized_dicts','setting_sync_clear_key'],'public_resource_ids_unchanged':True,
      'manifest_unchanged':True,'runtime_tested':False,'privacy_final':False,
      'explicit_limit':'Usage-metrics backend, federated remnants, and voice-donation promo/preference helpers remain for later passes.'}
def main():
    p=argparse.ArgumentParser();p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('--json',type=Path);a=p.parse_args();r=verify(a.before,a.after);s=json.dumps(r,indent=2)+'\n';
    if a.json:a.json.write_text(s)
    print(s)
if __name__=='__main__':main()
