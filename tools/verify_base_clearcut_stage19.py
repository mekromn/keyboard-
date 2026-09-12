#!/usr/bin/env python3
"""Independent source-preservation checks for the exact Stage-19 delta.

These checks do not execute Android bytecode. They verify that retained switch
bodies, conditional tails, shared constants, and all non-target class files have
not changed. This is intentionally separate from the patcher's own checks.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

if not __debug__:
    raise RuntimeError('Run without -O: verification assertions must stay enabled')

DELETED={'prl','psh','pri','prj','prk','prm','pse','psf'}
CASES={'daq':{2},'lsn':{17,18},'pdm':{9},'fjr':{12},'nwk':{17}}
CONDITIONAL={'jdz':':cond_2','jea':':cond_0','opu':':cond_1','mhc':':cond_8'}
METHOD=re.compile(r'(?ms)^\.method[^\n]*\n.*?^\.end method')


def normalize(text: str) -> str:
    return '\n'.join(l.strip() for l in text.splitlines()
                     if l.strip() and not l.lstrip().startswith(('.line ', '#')))


def method_map(text: str) -> dict:
    return {m[0].splitlines()[0]:m[0] for m in METHOD.finditer(text)}


def switch_parts(method: str) -> tuple:
    """Return prefix, default body, case bodies, and numeric dispatch mapping."""
    method=normalize(method)
    table=re.search(r'(?ms)^(:pswitch_data_\w+)\n\.(packed|sparse)-switch([^\n]*)\n(.*?)^\.end (?:packed|sparse)-switch',method)
    assert table, 'switch table missing'
    if table[2]=='packed':
        mapping=dict(enumerate(re.findall(r':pswitch_[0-9a-f]+',table[4]),int(table[3].strip(),0)))
    else:
        mapping={int(k,0):v for k,v in re.findall(r'(0x[0-9a-f]+) -> (:pswitch_[0-9a-f]+)',table[4])}
    code=method[:table.start()]
    labels=list(re.finditer(r'(?m)^(:pswitch_[0-9a-f]+)$',code))
    bodies={m[1]:code[m.start():labels[i+1].start() if i+1<len(labels) else len(code)].strip()
            for i,m in enumerate(labels)}
    header=code[:labels[0].start()]
    header=re.sub(r'\b(?:packed|sparse)-switch\b','SWITCH',header)
    return header,bodies,mapping


def verify(before:Path, after:Path) -> dict:
    b={p.relative_to(before).as_posix():p.read_text() for p in before.glob('smali*/**/*.smali')}
    a={p.relative_to(after).as_posix():p.read_text() for p in after.glob('smali*/**/*.smali')}
    assert not set(a)-set(b), 'class added'
    removed={Path(p).stem for p in set(b)-set(a)}
    assert removed==DELETED,(removed,DELETED)
    changed=[p for p in a if a[p]!=b[p]]
    assert {Path(p).stem for p in changed}==set(CASES)|set(CONDITIONAL)
    cases_checked=0
    for p in changed:
        cls=Path(p).stem
        bm,am=method_map(b[p]),method_map(a[p])
        assert bm.keys()==am.keys(),f'{cls}: changed method set'
        affected=[m for m in bm if bm[m]!=am[m]]
        assert len(affected)==1,f'{cls}: expected one changed method'
        mb,ma=bm[affected[0]],am[affected[0]]
        assert re.search(r'\.(?:locals|registers) \d+',mb)[0]==re.search(r'\.(?:locals|registers) \d+',ma)[0]
        if cls in CASES:
            bh,bb,bd=switch_parts(mb);ah,ab,ad=switch_parts(ma)
            assert bh==ah,f'{cls}: changed register setup/default branch'
            assert ad=={k:v for k,v in bd.items() if k not in CASES[cls]},f'{cls}: live selector mapping changed'
            for label in ad.values():
                assert bb[label]==ab[label],f'{cls}: live branch changed: {label}'
                cases_checked+=1
        else:
            nb,na=normalize(mb),normalize(ma)
            tail=CONDITIONAL[cls]
            assert nb[nb.index('\n'+tail+'\n'):]==na[na.index('\n'+tail+'\n'):],f'{cls}: retained tail changed'
            # Constants and register layout are unchanged, even where a now-dead
            # comparison used a constant also consumed by a different feature.
            def prefix_constants(t):
                cut=t.index('\n:cond_')
                return [l for l in t[:cut].splitlines() if l.startswith(('const','iget '))]
            if cls=='mhc':
                assert prefix_constants(nb)==prefix_constants(na),'mhc: live dictation register constant changed'
                early=nb[nb.index('\n:cond_0\n'):nb.index('\n:cond_5\n')]
                assert early in na,'mhc: dictation body changed'
    # All original non-code payload files are still exact in the decoded trees.
    for p in before.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(before)
        if rel.parts[0].startswith('smali') or rel.parts[0]=='build':continue
        other=after/rel
        assert other.is_file() and p.read_bytes()==other.read_bytes(),f'non-code changed: {rel}'
    return {'passed':True,'deleted_classes':sorted(removed),'modified_classes':sorted(Path(p).stem for p in changed),
            'untouched_classes':len(a)-len(changed),'retained_numeric_switch_cases_checked':cases_checked,
            'retained_conditional_tails_checked':len(CONDITIONAL),'shared_dictation_constant_preserved':True,
            'manifest_resources_assets_native_unchanged':True,'runtime_tested':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('--json',type=Path)
    args=p.parse_args();result=verify(args.before,args.after)
    text=json.dumps(result,indent=2)+'\n'
    if args.json:args.json.write_text(text)
    print(text)
if __name__=='__main__':main()
