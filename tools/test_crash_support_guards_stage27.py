#!/usr/bin/env python3
"""Mutation checks on disposable decoded trees only; restores every modified byte.
Run while no other process is accessing the supplied test trees. Does not touch
APKs, signing data, or the user's phone. Not an Android runtime test.
"""
from __future__ import annotations
import argparse,json,tempfile
from pathlib import Path
from remove_primes_crash_support_stage27 import apply,EXPECTED
from verify_primes_crash_support_stage27 import verify

def tests(baseline:Path,patched:Path)->dict:
    originals={e['path']:(baseline/e['path']).read_bytes() for e in EXPECTED.values()}
    results={}
    with tempfile.TemporaryDirectory() as temp:
        report=Path(temp)/'rejected.json'
        cases=[('new_retained_caller','smali/uab.smali',b'\n# mutation typed ingress Luec;\n'),
               ('changed_target','smali/uec.smali',b'\n# mutation file drift\n')]
        for name,rel,extra in cases:
            p=baseline/rel;old=p.read_bytes()
            try:
                p.write_bytes(old+extra)
                try:apply(baseline,report,False)
                except ValueError:results[name+'_rejected']=True
                else:raise AssertionError('Mutation accepted: '+name)
                assert all((baseline/r).is_file() for r in originals),'Deletion before failed preflight'
            finally:
                p.write_bytes(old)
                for r,data in originals.items():(baseline/r).write_bytes(data)
        p=patched/'smali/uab.smali';old=p.read_bytes()
        try:
            p.write_bytes(old+b'\n# unexpected retained-file mutation\n')
            try:verify(baseline,patched)
            except ValueError:results['retained_file_change_rejected']=True
            else:raise AssertionError('Independent comparison accepted a changed survivor')
        finally:p.write_bytes(old)
    assert verify(baseline,patched)['passed']
    return {'passed':True,'mutation_tests':results,'trees_restored_and_reverified':True,'runtime_tested':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline',type=Path);p.add_argument('patched',type=Path);p.add_argument('--json',type=Path)
    a=p.parse_args();result=tests(a.baseline,a.patched);text=json.dumps(result,indent=2)+'\n'
    if a.json:a.json.write_text(text)
    print(text)
if __name__=='__main__':main()
