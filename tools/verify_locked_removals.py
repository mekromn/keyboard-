#!/usr/bin/env python3
"""Verify locked Stage-28 removal invariants on an Apktool-decoded Meboard tree."""
from pathlib import Path
import argparse

def fail(msg): raise SystemExit('FAIL: '+msg)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); r=a.decoded
    smali='\n'.join(p.read_text(errors='replace') for p in r.glob('smali*/**/*.smali'))
    for x in ('Lrqw;','VoiceDonationManager','maybeAddDonationRequest','PrivacySettingsFragment;->aD(Z)V'):
        if x in smali: fail('removed marker returned: '+x)
    p=(r/'res/xml/setting_privacy.xml').read_text(errors='replace')
    for x in ('0x7f140a2d','0x7f140b93','0x7f140a2f'):
        if x in p: fail('removed privacy row returned: '+x)
    for x in ('0x7f140b2a','0x7f140d95'):
        if x not in p: fail('retained local privacy control missing: '+x)
    m=(r/'res/xml/APKTOOL_RENAMED_0x7f170002.xml').read_text(errors='replace')
    for x in ('enable_user_metrics','user_enable_federated_training'):
        if x in m: fail('removed managed restriction returned: '+x)
    print('PASS: locked Stage-28 removal invariants preserved')
if __name__=='__main__': main()
