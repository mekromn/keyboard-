#!/usr/bin/env python3
"""Independent comparison of Stage-20 method deletions and surviving flag dispatch.
Does not import the patcher. Operates on decoded files, not on-device execution.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

REMOVED={
 'aams':{'Z()Ljava/lang/String;','ad()Ljava/lang/String;','ar()Z'},
 'aamv':{'Z()Ljava/lang/String;','ad()Ljava/lang/String;','ar()Z'},
 'lgp':{'X()Ljava/lang/String;','Z()Ljava/lang/String;','aJ()Z'},
 'lhk':{'X()Ljava/lang/String;','Z()Ljava/lang/String;','aJ()Z'},
}
METHOD=re.compile(r'(?ms)^\.method[^\n]*\n.*?^\.end method')

def check(ok,message):
    if not ok:raise ValueError(message)

def mmap(text):return {s.splitlines()[0].split()[-1]:s for s in METHOD.findall(text)}

def code(body):
    return [l.strip() for l in body.splitlines() if l.strip() and not l.lstrip().startswith(('.line ','#'))]

def dispatch(body,selector):
    """Resolve the real numeric/default dispatch and collect straight-line result code."""
    lines=code(body)
    switch=next(i for i,s in enumerate(lines) if re.fullmatch(r'(packed|sparse)-switch p0, :pswitch_data_0',s))
    table=lines.index(':pswitch_data_0')
    kind=lines[table+1].split()[0];mapping={}
    if kind=='.packed-switch':
        base=int(lines[table+1].split()[1],0)
        entries=lines[table+2:lines.index('.end packed-switch')]
        mapping={base+i:label for i,label in enumerate(entries)}
    else:
        for line in lines[table+2:lines.index('.end sparse-switch')]:
            n,_,label=line.split();mapping[int(n,0)]=label
    pos=lines.index(mapping[selector])+1 if selector in mapping else switch+1
    result=[]
    for line in lines[pos:table]:
        if line.startswith(':') or line=='nop':continue
        result.append(line)
        if line.startswith('return-object '):break
    check(bool(result) and result[-1].startswith('return-object '),'no return in result case')
    check(not any(re.match(r'(if-|goto|packed-switch|sparse-switch)',s) for s in result),'unexpected nested control flow')
    setup=[s for s in lines[:switch] if not s.startswith('.line ')]
    return setup,result

def verify(before:Path,after:Path)->dict:
    b={p.relative_to(before).as_posix():p.read_bytes() for p in before.glob('smali*/**/*.smali')}
    a={p.relative_to(after).as_posix():p.read_bytes() for p in after.glob('smali*/**/*.smali')}
    check(a.keys()==b.keys(),'class set changed')
    changed={p for p in b if a[p]!=b[p]}
    expected={'smali/'+c+'.smali' for c in REMOVED}|{'smali_classes2/lhg.smali','smali_classes2/lhi.smali'}
    check(changed==expected,'unexpected changed-class set')
    kept_methods=0
    for path in changed:
        cls=Path(path).stem;bt=b[path].decode();at=a[path].decode();bm=mmap(bt);am=mmap(at)
        check(not set(am)-set(bm),'method added')
        check(set(bm)-set(am)==REMOVED.get(cls,set()),f'unexpected deleted methods {cls}')
        # Excludes whitespace from deleted methods, but preserves all declarations/fields.
        outside=lambda t:re.sub(r'\s+',' ',METHOD.sub('',t)).strip()
        check(outside(bt)==outside(at),f'class declaration or field change: {cls}')
        for sig in am:
            if cls in ['lhg','lhi'] and sig=='a()Ljava/lang/Object;':continue
            check(bm[sig]==am[sig],f'preserved method changed: {cls}->{sig}')
            kept_methods+=1
    cases=0
    for cls,removed in [('lhg',{20}),('lhi',{6,11})]:
        path='smali_classes2/'+cls+'.smali';sig='a()Ljava/lang/Object;'
        for value in set(range(21))-removed:
            check(dispatch(mmap(b[path].decode())[sig],value)==dispatch(mmap(a[path].decode())[sig],value),f'{cls} selector {value} changed')
            cases+=1
    # A text change must not have left a stale call to a removed interface method.
    for path,data in a.items():
        t=data.decode()
        for cls,sigs in REMOVED.items():
            check(not any('L'+cls+';->'+sig in t for sig in sigs),f'stale method reference in {path}')
    payload_files=0
    for p in before.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(before)
        if rel.parts[0].startswith('smali') or rel.parts[0]=='build':continue
        q=after/rel
        check(q.is_file() and p.read_bytes()==q.read_bytes(),f'non-code change: {rel}')
        payload_files+=1
    return {'passed':True,'unchanged_class_files':len(a)-len(changed),'changed_class_files':sorted(changed),
      'retained_methods_in_changed_classes_exact':kept_methods,'retained_supplier_selector_cases_checked':cases,
      'deleted_methods':{c:sorted(v) for c,v in REMOVED.items()},'non_smali_files_compared':payload_files,
      'classes_added':0,'classes_deleted':0,'no_removed_method_references':True,'runtime_tested':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('--json',type=Path)
    a=p.parse_args();s=json.dumps(verify(a.before,a.after),indent=2)+'\n'
    if a.json:a.json.write_text(s)
    print(s)
if __name__=='__main__':main()
