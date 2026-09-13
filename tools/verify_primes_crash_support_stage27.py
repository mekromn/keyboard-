#!/usr/bin/env python3
"""Independently prove the nine-file deletion and unchanged surviving file bytes.
Does not import the removal script. Does not execute the app or native code.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
DELETED={'smali/uaq.smali', 'smali/uec.smali', 'smali/ued.smali', 'smali/uad.smali', 'smali/uaf.smali', 'smali/uae.smali', 'smali/uag.smali', 'smali/uai.smali', 'smali/udx.smali'}
DESCRIPTORS={'Ludx;', 'Luad;', 'Luai;', 'Luag;', 'Lued;', 'Luec;', 'Luae;', 'Luaf;', 'Luaq;'}
MARKERS={'primes/crash','com/google/android/libraries/performance/primes/metrics/crash/CrashMetricFactory','CrashMetricFactory.java'}

def check(ok: bool,message: str) -> None:
    if not ok:raise ValueError(message)

def verify(before:Path,after:Path)->dict:
    b={p.relative_to(before).as_posix():p for p in before.rglob('*') if p.is_file() and p.relative_to(before).parts[0]!='build'}
    a={p.relative_to(after).as_posix():p for p in after.rglob('*') if p.is_file() and p.relative_to(after).parts[0]!='build'}
    check(set(b)-set(a)==DELETED,'Deletion set differs from nine reviewed files')
    check(not set(a)-set(b),'Files added')
    unchanged=0;other=0
    for name in a:
        bb=b[name].read_bytes();aa=a[name].read_bytes()
        check(bb==aa,'Surviving file changed: '+name)
        if name.endswith('.smali'):
            unchanged+=1
            check(not any(d.encode() in aa for d in DESCRIPTORS),'Dangling typed dependency')
            check(not any(m.encode() in aa for m in MARKERS),'Crash support marker survives')
        else:other+=1
    # Independent graph closure: scan all ORIGINAL files, not just current output.
    ingress={}
    originals={n:p.read_bytes() for n,p in b.items() if n.endswith('.smali')}
    for d in DESCRIPTORS:
        hits=sorted(n for n,data in originals.items() if d.encode() in data)
        check(set(hits)<=DELETED,'Target referenced from retained code')
        ingress[d]=hits
    check(unchanged==21745,'Unexpected surviving class count')
    return {'passed':True,'unchanged_class_files':unchanged,'unchanged_non_smali_files':other,
      'only_deleted_files':sorted(DELETED),'no_surviving_method_or_field_edits':True,
      'closed_inbound_graph':ingress,'runtime_tested':False,'privacy_final':False}

def main()->None:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('--json',type=Path)
    a=p.parse_args();text=json.dumps(verify(a.before,a.after),indent=2)+'\n'
    if a.json:a.json.write_text(text)
    print(text)
if __name__=='__main__':main()
