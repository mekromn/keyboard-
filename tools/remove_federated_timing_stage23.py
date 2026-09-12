#!/usr/bin/env python3
"""Exact Stage-22 -> Stage-23 physical federated timing/config excision.
No native/voice edits, no stubs, no new classes. Validate all edits before writing.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
INPUT_SHA = '8cf20fabd5ccba93aae7187fa27f4ffe3cbb3bed37a42c73d1e7c34c65db4766'
EXPECTED = {'smali/lnk.smali': 'e51f3a077c21a783e008ff990edac1f680bb7ebd9c22cf4f23ec369cd65feb7b', 'smali/lgp.smali': '75aa62d1f42b1794edcc8b48c963930618f6442807b7f89bbfaa70fdc2124243', 'smali/lhk.smali': '5dd1a7282ca628c68ed7f28f4767d3ed280070d436ac3be7286bedf0a1924b3c', 'smali/aams.smali': '51272d58866c79c44d189abe3efc02b09d118f7ebbec5a62f9ab1823e0a93a6d', 'smali/aamv.smali': '2948792f3e31dc0ea1c4fb2d2082b3a936d3515d657423c583293bfa5d607cc4', 'smali_classes2/lna.smali': '52d1703d6eba5e5c99b1ff02dfacdd2d177b61c7c5c17b25cc40b733c667f618', 'smali_classes2/lnc.smali': '63a4b2ca1e3d662fd8b1b2b4df583020ba2a55578e4a0568713db90ce969232e', 'smali_classes2/lhh.smali': '2800d3cf5336587734364d6bd563ea10d6446cd284430e1b4d811cc9437decce', 'smali_classes2/lhf.smali': 'f10648f96202e03362407e4da9a66515615723738922cfac789e360fd009c32e'}
METHOD = re.compile(r'(?ms)^\.method[^\n]*\n.*?^\.end method')
UPPER = {'E()J', 'K()J', 'N()J'}
LOWER = {'s()J', 'B()J', 'E()J'}
CASES = {'lhh': {6,10}, 'lhf': {12}}
FLAGS = (
 'TrainerFeature__inapp_training_max_scheduling_period_secs',
 'TrainerFeature__min_user_specified_scheduling_interval_sec_for_federated_computation',
 'TrainerFeature__max_user_specified_scheduling_interval_sec_for_federated_computation',
)
OLD_M='m(JIZ)J'; NEW_M='m(J)J'
OLD_H='h(JJLlgw;Z)Lzvi;'; NEW_H='h(JJLlgw;)Lzvi;'


def check(ok, message):
    if not ok: raise ValueError(message)


def sha(text): return hashlib.sha256(text.encode()).hexdigest()
def mmap(text): return {m.splitlines()[0].split()[-1]:m for m in METHOD.findall(text)}
def once(text, old, new):
    check(text.count(old)==1, 'unexpected count: '+old)
    return text.replace(old,new,1)


def prune_cases(text, cases):
    old=mmap(text)['a()Ljava/lang/Object;']
    tm=re.search(r'(?ms)(^[ \t]*(:pswitch_data_\w+)[ \t]*\n)[ \t]*\.packed-switch (0x\w+)\n(.*?)^[ \t]*\.end packed-switch',old)
    check(tm is not None, 'missing packed table')
    labels=re.findall(r':pswitch_[0-9a-f]+',tm[4]); mapping=dict(enumerate(labels,int(tm[3],0)))
    check(cases<=set(mapping), 'case absent')
    gone={mapping[x] for x in cases}
    check(not gone.intersection(v for k,v in mapping.items() if k not in cases), 'shared case label')
    replacement=tm[1]+'    .sparse-switch\n'+''.join(f'        0x{k:x} -> {v}\n' for k,v in mapping.items() if k not in cases)+'    .end sparse-switch'
    body=old[:tm.start()]+replacement+old[tm.end():]
    body=once(body, 'packed-switch p0, '+tm[2], 'sparse-switch p0, '+tm[2])
    table_start=re.search(r'(?m)^[ \t]*'+tm[2]+r'[ \t]*$',body).start()
    code_labels=list(re.finditer(r'(?m)^[ \t]*(:pswitch_[0-9a-f]+)[ \t]*$',body[:table_start]))
    spans=[(m.start(),code_labels[i+1].start() if i+1<len(code_labels) else table_start)
           for i,m in enumerate(code_labels) if m[1] in gone]
    check(len(spans)==len(gone),'case body count')
    for a,b in reversed(spans):
        removed_labels=re.findall(r'(?m)^[ \t]*(:\w+)[ \t]*$',body[a:b])
        rest=body[:a]+body[b:]
        check(not any(re.search(re.escape(l)+r'(?!\w)',rest) for l in removed_labels),'retained incoming branch')
        body=rest
    return once(text,old,body)


def transform_scheduler(text):
    methods=mmap(text); m=methods[OLD_M]
    # Keep precisely the original local branch and the shared min/max tail.
    start=re.search(r'(?m)^[ \t]*:cond_1[ \t]*$',m).end()
    body=m[start:]
    body=re.sub(r'\bp3\b','v3',body); body=re.sub(r'\bp4\b','v4',body)
    body=re.sub(r'(?m)^[ \t]*:goto_0[ \t]*\n','',body)
    new='.method public final '+NEW_M+'\n    .locals 5\n'+body
    text=once(text,m,new)
    h=methods[OLD_H]; newh=once(h,OLD_H,NEW_H)
    newh=once(newh,'invoke-virtual {p0, v4, v5, v3, p6}, Llnk;->'+OLD_M,
                      'invoke-virtual {p0, v4, v5}, Llnk;->'+NEW_M)
    # p5/p6 was a wide TEMPORARY after the call. p6 no longer exists. Reuse
    # the consumed interval pair v4/v5, without touching the options object p5.
    newh=once(newh,'move-result-wide p5','move-result-wide v4')
    newh=once(newh,'add-long/2addr p1, p5','add-long/2addr p1, v4')
    newh=once(newh,'add-long/2addr p3, p5','add-long/2addr p3, v4')
    check(not re.search(r'\bp6\b',newh), 'stale removed parameter')
    return once(text,h,newh)


def supplier_uses(text,cls):
    uses=[]
    for signature,body in mmap(text).items():
        ls=[x.strip() for x in body.splitlines() if x.strip() and not x.lstrip().startswith(('.line ','#'))]
        for i,line in enumerate(ls):
            m=re.fullmatch(r'invoke-direct \{[vp]\d+, ([vp]\d+)\}, L'+cls+r';-><init>\(I\)V',line)
            if m:
                c=re.fullmatch(r'const(?:/4|/16)? '+m[1]+r', (-?0x[0-9a-f]+|-?\d+)',ls[i-1])
                check(c is not None, 'unknown supplier producer')
                uses.append((signature,int(c[1],0)))
    return uses


def apply(root:Path,report:Path,dry_run=False):
    before={p.relative_to(root).as_posix():p.read_text() for p in root.glob('smali*/**/*.smali')}
    check(len(before)==21761, 'not Stage-22 class count')
    for p,h in EXPECTED.items():check(p in before and sha(before[p])==h,'input drift '+p)
    for interface,impl in [('lgp','lhk'),('aams','aamv')]:
        users={p for p,t in before.items() if re.search(r'^\.implements L'+interface+r';$',t,re.M)}
        check(users=={f'smali/{impl}.smali'},'unexpected interface implementation')
    # Scope/reference guards are independent of the names of the flags.
    for cls,sigs in [('lgp',UPPER),('lhk',UPPER),('aams',LOWER),('aamv',LOWER)]:
        for sig in sigs:
            paths={p for p,t in before.items() if 'L'+cls+';->'+sig in t}
            expected=({'smali/lnk.smali'} if cls=='lgp' else
                      {f'smali_classes2/{"lhf" if sig=="B()J" else "lhh"}.smali'} if cls=='aams' else set())
            check(paths==expected,'new config consumer: '+cls+'->'+sig)
    for cls,cases in CASES.items():
        check({p for p,t in before.items() if f'L{cls};-><init>' in t}=={'smali/lhk.smali'},'new supplier construction')
        selected={sig for sig,n in supplier_uses(before['smali/lhk.smali'],cls) if n in cases}
        check(selected==({'E()J','N()J'} if cls=='lhh' else {'K()J'}),'new supplier selector use')
    check({p for p,t in before.items() if 'Llnk;->'+OLD_M in t}=={'smali/lnk.smali','smali_classes2/lna.smali','smali_classes2/lnc.smali'},'new timing consumer')
    check({p for p,t in before.items() if 'Llnk;->'+OLD_H in t}=={'smali_classes2/lna.smali'},'new deadline consumer')
    after=dict(before)
    after['smali/lnk.smali']=transform_scheduler(before['smali/lnk.smali'])
    path='smali_classes2/lna.smali'; t=after[path]
    check(t.count('invoke-virtual/range {v5 .. v11}, Llnk;->'+OLD_H)==2,'deadline call count')
    t=t.replace('invoke-virtual/range {v5 .. v11}, Llnk;->'+OLD_H,'invoke-virtual/range {v5 .. v10}, Llnk;->'+NEW_H)
    t=once(t,'invoke-virtual {v5, v8, v9, v3, v7}, Llnk;->'+OLD_M,'invoke-virtual {v5, v8, v9}, Llnk;->'+NEW_M)
    after[path]=t
    path='smali_classes2/lnc.smali'
    after[path]=once(after[path],'invoke-virtual {v6, v8, v9, v3, v7}, Llnk;->'+OLD_M,'invoke-virtual {v6, v8, v9}, Llnk;->'+NEW_M)
    for cls,sigs in [('lgp',UPPER),('lhk',UPPER),('aams',LOWER),('aamv',LOWER)]:
        p=f'smali/{cls}.smali'; mm=mmap(after[p])
        for sig in sigs:after[p]=once(after[p],mm[sig],'')
    for cls,cases in CASES.items():
        p=f'smali_classes2/{cls}.smali'; after[p]=prune_cases(after[p],cases)
    forbidden=['Llnk;->'+OLD_M,'Llnk;->'+OLD_H,*FLAGS]
    for cls,sigs in [('lgp',UPPER),('lhk',UPPER),('aams',LOWER),('aamv',LOWER)]:
        forbidden += ['L'+cls+';->'+sig for sig in sigs]
    for p,t in after.items():check(not any(n in t for n in forbidden),'residual reference '+p)
    changed=sorted(p for p in before if before[p]!=after[p]); check(set(changed)==set(EXPECTED),'edit scope')
    result={'input_sha256':INPUT_SHA,'classes_before':len(before),'classes_after':len(after),
            'modified_files':changed,'unchanged_class_files':len(before)-len(changed),
            'deleted_config_methods':12,'deleted_supplier_cases':{c:sorted(v) for c,v in CASES.items()},
            'reduced_timing_methods':{OLD_M:NEW_M,OLD_H:NEW_H},'removed_flags':list(FLAGS),
            'net_smali_bytes_removed':sum(len(before[p].encode())-len(after[p].encode()) for p in changed),
            'before_hashes':{p:sha(before[p]) for p in changed},'after_hashes':{p:sha(after[p]) for p in changed},
            'native_modified':False,'voice_fix_claimed':False,'runtime_tested':False,'privacy_final':False,'dry_run':dry_run}
    if not dry_run:
        for p in changed:(root/p).write_text(after[p])
    report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--report',type=Path,required=True);p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    print(json.dumps(apply(a.root,a.report,a.dry_run),indent=2))
if __name__=='__main__':main()
