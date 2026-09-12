#!/usr/bin/env python3
"""Physically excise the federated completion/retry rescheduler from pinned Stage 20.

Deletes lnf and lnk.t, reduces lnk.f to a local-only dispatcher, and removes its
server-retry argument at all three typed call sites. Unsupported job types throw
explicitly: they are not silently reinterpreted as local jobs or ignored.
The initial mixed scheduler and native configuration are NOT changed by this pass.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

INPUT_SHA = '05f16f7e94c17426a988961e15856059ba82b30a30e4dd992ae1d14a757fc7e3'
EXPECTED = {
 'smali/lnk.smali':'97b08807d79e9493e1c17fcc4cf151e2b613075b289578dee6dd710c18987945',
 'smali_classes2/lnf.smali':'d47d620eadc666487d3f4dc5a9b1861452bed7228e0128eb5bcac125d0ca876f',
 'smali_classes2/lkc.smali':'37eb8d556cbb5caeca7a8452d593d51d7c2d95d565586ef507a37e8b0e3838f9',
 'smali_classes2/com/google/android/gms/learning/dynamite/training/InAppJobServiceImpl.smali':'e6993a9f831e85324f0866fff2c0ff9031b270aa17750e1c266005042e228414',
 'smali_classes2/lkd.smali':'8812c144f7836e2226062a7b98a8bffec5a6a235e97029344793dd7fbf8d992d',
 'smali_classes2/liu.smali':'9f8eed9f90ad2b2d2f57f3320ae56bde6b131b6e19a78a432d443def1aae9ebb',
 'smali_classes2/lis.smali':'3118043e63077b43357009abcc7eca58278b37629ee4cfde3389afd821795de3',
 'smali_classes2/lit.smali':'9ced54ce3725880b6e49d3e6b3bd3864bae5c9c4ba303f6dccbc07baca2140c5',
 'smali_classes2/jyk.smali':'562da06144311891de843b9cb4d9da109eda6fc8e50c2179bcf920562b04fce1',
 'smali_classes2/lnc.smali':'63a4b2ca1e3d662fd8b1b2b4df583020ba2a55578e4a0568713db90ce969232e',
}
OLD='f(ILjava/lang/String;Llkd;Lynz;I)Lwzc;'
NEW='f(ILjava/lang/String;Llkd;I)Lwzc;'
FACTORY='t(ILjava/lang/String;Llkd;Lynz;I)Lwyv;'
METHOD=re.compile(r'(?ms)^\.method[^\n]*\n.*?^\.end method')
SPACE=r'(?:\s|\.line \d+)*'
JOB='smali_classes2/com/google/android/gms/learning/dynamite/training/InAppJobServiceImpl.smali'
GUARD='''    invoke-virtual {p3}, Llkd;->b()I
    move-result v0
    const/4 v1, 0x2
    if-eq v0, v1, :cond_0

    new-instance v1, Ljava/lang/UnsupportedOperationException;
    invoke-static {v0}, Ljyk;->n(I)Ljava/lang/String;
    move-result-object v0
    invoke-direct {v1, v0}, Ljava/lang/UnsupportedOperationException;-><init>(Ljava/lang/String;)V
    throw v1

    :cond_0
    invoke-direct {p0, p1, p2, p3, p4}, Llnk;->u(ILjava/lang/String;Llkd;I)Lwyv;
    move-result-object p1

'''


def require(ok:bool, message:str)->None:
    if not ok:raise ValueError(message)


def digest(text:str)->str:return hashlib.sha256(text.encode()).hexdigest()

def method_map(text:str)->dict[str,str]:
    return {b.splitlines()[0].split()[-1]:b for b in METHOD.findall(text)}


def labels_valid(text:str)->None:
    for body in METHOD.findall(text):
        code=re.sub(r'"(?:\\.|[^"\\])*"','""',body)
        code=re.sub(r'(?m)#.*$','',code)
        labels=re.findall(r'(?m)^\s*(:\w+)\s*$',code)
        require(len(labels)==len(set(labels)),'duplicate label')
        targets=set(re.findall(r'(?<![\w]):(?:cond|goto|try_start|try_end|catch|catchall|pswitch|sswitch|array)_[\w]+',code))
        require(targets <= set(labels),'unresolved control-flow label')


def apply(root:Path, report:Path, dry_run:bool=False)->dict:
    before={p.relative_to(root).as_posix():p.read_text() for p in root.glob('smali*/**/*.smali')}
    require(len(before)==21762,'wrong input class count')
    for p,h in EXPECTED.items():require(p in before and digest(before[p])==h,'input drift: '+p)
    descriptor_refs={p for p,t in before.items() if 'Llnf;' in t}
    require(descriptor_refs=={'smali/lnk.smali','smali_classes2/lnf.smali'},'new federated helper caller')
    require({p for p,t in before.items() if 'Llnk;->'+FACTORY in t}=={'smali/lnk.smali'},'new factory caller')
    require({p:t.count('Llnk;->'+OLD) for p,t in before.items() if 'Llnk;->'+OLD in t}
            =={'smali_classes2/lkc.smali':1,JOB:2},'dispatch callers changed')
    require(not any(re.search(r'const-string(?:/jumbo)?[^\n]*"(?:lnf|lnk|Llnf;|Llnk;)"',t) for t in before.values()),'reflective literal requires review')
    after=dict(before)
    scheduler=after['smali/lnk.smali'];mm=method_map(scheduler)
    require(OLD in mm and FACTORY in mm and NEW not in mm,'scheduler method set drifted')
    old=mm[OLD];a=old.index('    invoke-virtual {p3}, Llkd;->b()I');b=old.index('    :goto_0')
    new=(old[:a]+GUARD+old[b:]).replace(OLD,NEW,1)
    require(not re.search(r'\bp5\b',new),'old register parameter survived')
    scheduler=scheduler.replace(mm[FACTORY],'',1).replace(old,new,1)
    after['smali/lnk.smali']=scheduler
    call=re.escape('invoke-virtual/range {v0 .. v5}, Llnk;->'+OLD)
    rx=re.compile(r'    move-object v4, p2'+SPACE+r'move v5, p3'+SPACE+call)
    after['smali_classes2/lkc.smali'],n=rx.subn(
        '    move v4, p3\n    invoke-virtual/range {v0 .. v4}, Llnk;->'+NEW,after['smali_classes2/lkc.smali'])
    require(n==1,'expected one completion caller')
    rx=re.compile(r'    const/4 v4, 0x0'+SPACE+r'const/4 v5, 0x1'+SPACE+call)
    after[JOB],n=rx.subn('    const/4 v4, 0x1\n    invoke-virtual/range {v0 .. v4}, Llnk;->'+NEW,after[JOB])
    require(n==2,'expected two job-service callers')
    del after['smali_classes2/lnf.smali']
    changed=sorted(p for p in after if after[p]!=before[p])
    require(set(changed)=={'smali/lnk.smali','smali_classes2/lkc.smali',JOB},'unexpected edit scope')
    for p in changed:labels_valid(after[p])
    for p,t in after.items():
        require('Llnf;' not in t and 'Llnk;->'+FACTORY not in t and 'Llnk;->'+OLD not in t,'removed reference remains: '+p)
    result={'input_apk_sha256':INPUT_SHA,'classes_before':len(before),'classes_after':len(after),
      'deleted_classes':['lnf'],'modified_files':changed,'untouched_class_files':len(after)-len(changed),
      'deleted_factory':FACTORY,'old_dispatch_signature':OLD,'new_dispatch_signature':NEW,
      'callsites_migrated':3,'unsupported_nonlocal_jobs':'explicit UnsupportedOperationException; never rerouted',
      'retained_local_rescheduler_byte_identical':True,'initial_scheduler_unchanged':True,
      'local_interval_math_unchanged':True,'native_configuration_unchanged':True,
      'deleted_smali_bytes':len(before['smali_classes2/lnf.smali'].encode()),
      'net_smali_bytes_removed':sum(len(t.encode()) for t in before.values())-sum(len(t.encode()) for t in after.values()),
      'before_hashes':{p:digest(before[p]) for p in changed+['smali_classes2/lnf.smali']},
      'after_hashes':{p:digest(after[p]) for p in changed},'dry_run':dry_run,
      'runtime_tested':False,'privacy_final':False}
    if not dry_run:
        for p in changed:(root/p).write_text(after[p])
        (root/'smali_classes2/lnf.smali').unlink()
    report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    p.add_argument('--report',type=Path,required=True);p.add_argument('--dry-run',action='store_true')
    a=p.parse_args();print(json.dumps(apply(a.root,a.report,a.dry_run),indent=2))
if __name__=='__main__':main()
