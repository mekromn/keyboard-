#!/usr/bin/env python3
"""Independent Stage-25 factory preservation and call-site reachability checks.

Does not import the patcher. Checks exact retained bodies and all four producer
selectors with a conservative single-register CFG. These are static checks,
not Android execution and not universal reflection/native reachability proof.
"""
from __future__ import annotations
import argparse, collections, json, re
from pathlib import Path
M = re.compile(r'(?ms)^\.method[^\n]*\n.*?^\.end method')
FACTORY='smali/tgh.smali';PRODUCER='smali/pli.smali'
DELETED={'smali/udo.smali','smali_classes3/udn.smali','smali_classes3/udh.smali'}
CTOR='<init>(Laals;Laals;Laals;Laals;Laals;Laals;Laals;I[S)V'
LIVE_CTOR='<init>(Ltgg;Laals;Laals;Laals;Laals;Laals;Laals;I)V'


def check(ok, message):
    if not ok: raise ValueError(message)


def mmap(text): return {b.splitlines()[0].split()[-1]:b for b in M.findall(text)}


def prove_producers(text):
    """Read selector v21 along every path to the four range constructor calls."""
    methods=[m for m in M.findall(text) if 'Ltgh;-><init>' in m]
    check(len(methods)==1,'unexpected producer method set')
    body=methods[0]
    check('.locals 64' in body, 'v21/parameter alias assumptions changed')
    check('.catch' not in body and '-switch' not in body, 'unsupported producer CFG')
    c=[s.strip() for s in body.splitlines() if s.strip() and not s.lstrip().startswith(('.', '#'))]
    labels={s:i for i,s in enumerate(c) if s.startswith(':')}
    U='unknown';states={0:U};todo=collections.deque([0]);steps=0
    while todo:
        i=todo.popleft();val=states[i];s=c[i];op=s.split()[0];out=val
        no_dest=s.startswith(':') or op.startswith(('invoke','iput','sput','aput','if-','goto','return','throw','monitor','check-cast','filled-new-array','fill-array-data'))
        if not no_dest:
            match=re.match(r'\S+ ([vp]\d+)',s)
            check(match is not None or op=='nop','unmodelled producer opcode '+s)
            if match:
                dest=match[1]
                wide=('wide' in op or (('-long' in op or '-double' in op) and not op.startswith('cmp')))
                if dest=='v21' or (wide and dest=='v20'):
                    literal=re.fullmatch(r'const(?:/4|/16)? v21, (-?0x[0-9a-f]+|-?\d+)',s)
                    out=int(literal[1],0) if literal else U
                    if re.fullmatch(r'move(?:/from16|/16)? v21, v21',s):out=val
        if op.startswith('goto'):targets=[labels[s.split()[-1]]]
        elif op.startswith(('return','throw')):targets=[]
        elif op.startswith('if-'):targets=[i+1,labels[s.split()[-1]]]
        else:targets=[i+1]
        for j in targets:
            if j>=len(c):continue
            merged=out if j not in states else states[j] if states[j]==out else U
            if j not in states or states[j]!=merged:states[j]=merged;todo.append(j)
        steps+=1;check(steps<100000,'producer CFG did not converge')
    values=[]
    for i,s in enumerate(c):
        if 'Ltgh;-><init>' in s:
            check(s=='invoke-direct/range {v13 .. v21}, Ltgh;->'+LIVE_CTOR,'unknown factory construction')
            v=states.get(i,U);check(type(v)==int and 0<=v<=6,'caller can enter deleted default')
            values.append(v)
    check(values==[3,0,2,1],'producer selectors changed')
    return {'typed_constructor_sites':len(values),'selectors':values,'no_reporting_default_reachable':True,
            'cfg_steps':steps,'method':body.splitlines()[0]}


def verify(before:Path,after:Path):
    b={p.relative_to(before).as_posix():p.read_text() for p in before.glob('smali*/**/*.smali')}
    a={p.relative_to(after).as_posix():p.read_text() for p in after.glob('smali*/**/*.smali')}
    check(set(b)-set(a)==DELETED and not set(a)-set(b),'wrong class deletion/addition')
    check([p for p in a if a[p]!=b[p]]==[FACTORY],'unexpected surviving-class change')
    old=mmap(b[FACTORY]);new=mmap(a[FACTORY])
    check(set(old)-set(new)=={CTOR} and not set(new)-set(old),'wrong removed method')
    check(not any('Ltgh;->'+CTOR in t for t in b.values()),'deleted ctor has typed callers')
    checked=0
    for sig in new:
        if sig!='iM()Ljava/lang/Object;':check(new[sig]==old[sig],'retained constructor changed');checked+=1
    # Remove whole methods to compare class/interface/field declarations.
    normalize=lambda t:re.sub(r'\s+',' ',M.sub('',t)).strip()
    check(normalize(b[FACTORY])==normalize(a[FACTORY]),'fields or declarations changed')
    o,n=old['iM()Ljava/lang/Object;'],new['iM()Ljava/lang/Object;']
    pivot='    packed-switch v0, :pswitch_data_0'
    check(o[:o.index(pivot)+len(pivot)]==n[:n.index(pivot)+len(pivot)],'dispatch/register setup changed')
    label='    :pswitch_0\n'
    check(o[o.index(label):]==n[n.index(label):],'retained factory bodies or table changed')
    default=n[n.index(pivot)+len(pivot):n.index(label)]
    ops=[s.strip() for s in default.splitlines() if s.strip() and not s.lstrip().startswith(('.', '#'))]
    check(ops==[
     'new-instance v0, Ljava/lang/UnsupportedOperationException;',
     'const-string v1, "Unsupported provider selector"',
     'invoke-direct {v0, v1}, Ljava/lang/UnsupportedOperationException;-><init>(Ljava/lang/String;)V',
     'throw v0'], 'default is not a pure rejection')
    table=re.search(r'(?ms)\.packed-switch 0x0\n(.*?)\.end packed-switch',n)
    check(table is not None and re.findall(r':pswitch_[0-9a-f]+',table[1])==
          [':pswitch_6',':pswitch_5',':pswitch_4',':pswitch_3',':pswitch_2',':pswitch_1',':pswitch_0'], 'selector mapping changed')
    callers={p for p,t in b.items() if 'Ltgh;' in t}-{FACTORY}
    check(callers=={PRODUCER},'new factory reference')
    proof=prove_producers(b[PRODUCER]);check(b[PRODUCER]==a[PRODUCER],'producer changed')
    # Mutation sensitivity: selecting the removed factory must be rejected.
    mutation=b[PRODUCER].replace('const/16 v21, 0x3','const/16 v21, 0x7',1)
    try:prove_producers(mutation)
    except ValueError:pass
    else:raise ValueError('CFG missed deliberate reporting-selector mutation')
    for p,t in a.items():
        check(not any('L'+name+';' in t for name in ['udo','udn','udh']), 'dangling descriptor in '+p)
    count=0
    for p in before.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(before)
        if rel.parts[0].startswith('smali') or rel.parts[0]=='build':continue
        q=after/rel;check(q.is_file() and p.read_bytes()==q.read_bytes(), 'non-code change '+str(rel));count+=1
    return {'passed':True,'deleted_classes':['udo','udn','udh'],'modified_class':'tgh',
            'unchanged_class_files':len(a)-1,'retained_constructor_methods_exact':checked,
            'retained_factory_cases_exact':7,'producer_proof':proof,'selector_mutation_detected':True,
            'compiled_or_phone_runtime_test':False,'non_smali_files_compared':count,
            'voice_classes_and_native_unchanged':True,'privacy_final':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('before',type=Path);p.add_argument('after',type=Path)
    p.add_argument('--json',type=Path);a=p.parse_args();result=verify(a.before,a.after);out=json.dumps(result,indent=2)+'\n'
    if a.json:a.json.write_text(out)
    print(out)

if __name__=='__main__':main()
