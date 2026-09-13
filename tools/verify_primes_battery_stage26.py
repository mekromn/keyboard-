#!/usr/bin/env python3
"""Independent file-preservation check; does not import the deletion script."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
REMOVED={'smali/tys.smali','smali/tyr.smali','smali_classes3/tyq.smali','smali/tzb.smali'}

def require(ok,why):
    if not ok:raise ValueError(why)

def compare(before:dict,after:dict)->dict:
    require(not set(after)-set(before),'Files added')
    require(set(before)-set(after)==REMOVED,'Unexpected deletion set')
    require(all(after[p]==before[p] for p in after),'Surviving file modified')
    for p,content in after.items():
        if p.endswith('.smali'):
            require(not re.search(rb'L(?:tys|tyr|tyq|tzb);',content),'Deleted descriptor still referenced')
    retained=sum(p.endswith('.smali') and p.split('/')[0].startswith('smali') for p in after)
    return {'passed':True,'deleted_files':sorted(REMOVED),'unchanged_surviving_class_files':retained,
            'unchanged_other_decoded_files':len(after)-retained,'new_files':0,'changed_surviving_files':0,'runtime_tested':False}

def read_tree(path):
    return {p.relative_to(path).as_posix():p.read_bytes() for p in path.rglob('*') if p.is_file() and p.relative_to(path).parts[0]!='build'}

def verify(before:Path,after:Path):
    b,a=read_tree(before),read_tree(after);result=compare(b,a)
    target=next(p for p in a if p.endswith('.smali'));bad=dict(a);bad[target]+=b'\n# mutation\n'
    try:compare(b,bad)
    except ValueError:result['retained_file_mutation_detected']=True
    else:raise ValueError('Verifier failed to detect mutation')
    bad=dict(a);p=next(iter(REMOVED));bad[p]=b[p]
    try:compare(b,bad)
    except ValueError:result['missing_deletion_mutation_detected']=True
    else:raise ValueError('Verifier failed to detect undeleted class')
    require(result['unchanged_surviving_class_files']==21754,'Unexpected retained class count')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('--json',type=Path);a=p.parse_args();r=verify(a.before,a.after);s=json.dumps(r,indent=2)+'\n'
    if a.json:a.json.write_text(s)
    print(s)
if __name__=='__main__':main()
