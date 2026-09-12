#!/usr/bin/env python3
"""Independent source/dispatch checks for Stage 21, without importing its patcher.
This is structural and symbolic verification, not execution on Android/ART.
"""
from __future__ import annotations
import argparse, itertools, json, re
from pathlib import Path

METHOD=re.compile(r'(?ms)^\.method[^\n]*\n.*?^\.end method')
OLD='f(ILjava/lang/String;Llkd;Lynz;I)Lwzc;'
NEW='f(ILjava/lang/String;Llkd;I)Lwzc;'
FACTORY='t(ILjava/lang/String;Llkd;Lynz;I)Lwyv;'
JOB='smali_classes2/com/google/android/gms/learning/dynamite/training/InAppJobServiceImpl.smali'

def check(ok,message):
    if not ok:raise ValueError(message)

def methods(t):return {m.splitlines()[0].split()[-1]:m for m in METHOD.findall(t)}

def normalized(t):return '\n'.join(l.strip() for l in t.splitlines() if l.strip() and not l.strip().startswith(('.line ','#')))

def dispatch(body,kind,job_id,session,status,new):
    """Interpret only the reviewed straight-line/conditional pre-dispatch subset."""
    lines=normalized(body).splitlines()
    regs={'p0':'scheduler','p1':job_id,'p2':session,'p3':('options',kind),
          'p4':status if new else 'server_result_ignored_for_local','p5':status}
    labels={l:i for i,l in enumerate(lines) if l.startswith(':')}
    result=None;i=0;steps=0
    while i<len(lines):
        steps+=1;check(steps<100,'unexpected loop in dispatcher')
        s=lines[i];i+=1
        if s.startswith(('.',':','monitor-enter ')):continue
        if s=='invoke-virtual {p3}, Llkd;->b()I':result=kind;continue
        m=re.fullmatch(r'move-result(?:-object)? ([vp]\d+)',s)
        if m:regs[m[1]]=result;continue
        m=re.fullmatch(r'const/4 ([vp]\d+), (0x[0-9a-f]+)',s)
        if m:regs[m[1]]=int(m[2],0);continue
        m=re.fullmatch(r'if-(eq|ne) ([vp]\d+), ([vp]\d+), (:\w+)',s)
        if m:
            take=(regs[m[2]]==regs[m[3]])==(m[1]=='eq')
            if take:i=labels[m[4]]
            continue
        m=re.fullmatch(r'invoke-direct \{([^}]+)\}, Llnk;->u\(ILjava/lang/String;Llkd;I\)Lwyv;',s)
        if m:return 'local',[regs[r.strip()] for r in m[1].split(',')]
        if s.startswith('invoke-direct/range ') and 'Llnk;->'+FACTORY in s:return 'federated',None
        if s=='new-instance v1, Ljava/lang/UnsupportedOperationException;':regs['v1']='UnsupportedOperationException';continue
        if s=='invoke-static {v0}, Ljyk;->n(I)Ljava/lang/String;':result='FEDERATED_TRAINING_OPTIONS' if regs['v0']==1 else 'PERSONALIZED_TRAINING_OPTIONS';continue
        if s=='invoke-direct {v1, v0}, Ljava/lang/UnsupportedOperationException;-><init>(Ljava/lang/String;)V':continue
        if s=='throw v1':return 'rejected',regs['v1']
        raise ValueError('unreviewed dispatch instruction: '+s)
    raise ValueError('dispatch did not terminate')


def verify(before:Path,after:Path)->dict:
    b={p.relative_to(before).as_posix():p.read_text() for p in before.glob('smali*/**/*.smali')}
    a={p.relative_to(after).as_posix():p.read_text() for p in after.glob('smali*/**/*.smali')}
    check(not set(a)-set(b),'class added')
    check(set(b)-set(a)=={'smali_classes2/lnf.smali'},'wrong deleted class set')
    changed={p for p in a if a[p]!=b[p]}
    check(changed=={'smali/lnk.smali','smali_classes2/lkc.smali',JOB},'wrong edit set')
    unchanged_methods=0
    for p in changed:
        bm=methods(b[p]);am=methods(a[p])
        if p=='smali/lnk.smali':
            check(set(bm)-set(am)=={OLD,FACTORY} and set(am)-set(bm)=={NEW},'scheduler API delta differs')
            affected={OLD,FACTORY,NEW}
        else:
            check(bm.keys()==am.keys(),'caller method set changed')
            affected={'d(Llkb;Lynz;IZ)V'} if p.endswith('/lkc.smali') else {'onStartJob(Landroid/app/job/JobParameters;)Z'}
        for sig in set(am)&set(bm)-affected:
            check(am[sig]==bm[sig],f'unrelated method changed: {p}/{sig}');unchanged_methods+=1
        check(normalized(METHOD.sub('',b[p]))==normalized(METHOD.sub('',a[p])),'fields or class declaration changed')
    # Expand each new call back into the old argument layout. Everything else,
    # including conditionals, catches, cancellation and jobFinished, must match.
    for p in ['smali_classes2/lkc.smali',JOB]:
        nb=normalized(b[p]);na=normalized(a[p])
        if p.endswith('/lkc.smali'):
            new='move v4, p3\ninvoke-virtual/range {v0 .. v4}, Llnk;->'+NEW
            old='move-object v4, p2\nmove v5, p3\ninvoke-virtual/range {v0 .. v5}, Llnk;->'+OLD
            count=1
        else:
            new='const/4 v4, 0x1\ninvoke-virtual/range {v0 .. v4}, Llnk;->'+NEW
            old='const/4 v4, 0x0\nconst/4 v5, 0x1\ninvoke-virtual/range {v0 .. v5}, Llnk;->'+OLD
            count=2
        check(na.count(new)==count,'migrated call count differs')
        check(na.replace(new,old)==nb,'caller changed beyond server-argument removal')
    old=normalized(methods(b['smali/lnk.smali'])[OLD]);new=normalized(methods(a['smali/lnk.smali'])[NEW])
    check(old[old.index('\n:goto_0\n'):]==new[new.index('\n:goto_0\n'):],'future/error/monitor tail changed')
    check(old[:old.index('invoke-virtual {p3}')].replace(OLD,NEW)==new[:new.index('invoke-virtual {p3}')],'scheduler monitor setup changed')
    # Enumerate independent combinations of job IDs, session identities and
    # result codes: compare actual register arguments at the retained u() call.
    samples=0
    for job_id,session,status in itertools.product([-2147483648,-1,0,1,2147483647],[None,'','local-model'],[-2147483648,-1,0,1,2,2147483647]):
        lhs=dispatch(old,2,job_id,session,status,False)
        rhs=dispatch(new,2,job_id,session,status,True)
        check(lhs==rhs==('local',['scheduler',job_id,session,('options',2),status]),'local argument mismatch')
        samples+=1
    for kind in [-2147483648,-1,0,1,3,2147483647]:
        check(dispatch(new,kind,0,'local',0,True)==('rejected','UnsupportedOperationException'),'nonlocal input was not rejected')
    for p,t in a.items():
        check('Llnf;' not in t and 'Llnk;->'+FACTORY not in t and 'Llnk;->'+OLD not in t,'stale removed reference: '+p)
    noncode=0
    for p in before.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(before)
        if rel.parts[0].startswith('smali') or rel.parts[0]=='build':continue
        q=after/rel;check(q.is_file() and p.read_bytes()==q.read_bytes(),'noncode changed: '+str(rel));noncode+=1
    return {'passed':True,'deleted_classes':['lnf'],'modified_class_files':sorted(changed),
      'untouched_class_files':len(a)-len(changed),'unchanged_methods_in_modified_classes':unchanged_methods,
      'local_dispatch_argument_cases_checked':samples,'unsupported_job_types_checked':6,
      'migrated_callsites_checked':3,'local_rescheduler_byte_identical':True,
      'local_interval_math_and_settings_byte_identical':True,'initial_scheduler_and_native_configuration_unchanged':True,
      'async_future_exception_and_monitor_tail_unchanged':True,'non_smali_files_compared':noncode,
      'no_deleted_descriptor_references':True,'runtime_tested':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('--json',type=Path)
    a=p.parse_args();s=json.dumps(verify(a.before,a.after),indent=2)+'\n'
    if a.json:a.json.write_text(s)
    print(s)
if __name__=='__main__':main()
