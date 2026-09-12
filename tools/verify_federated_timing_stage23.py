#!/usr/bin/env python3
"""Independent Stage-23 source/CFG/register/arithmetic preservation checks.
No patcher import. The bounded interpreter is not an Android VM; external
configuration/enum/timestamp calls are modelled, not executed on a device.
"""
from __future__ import annotations
import argparse,collections,itertools,json,random,re
from pathlib import Path
M=re.compile(r'(?ms)^\.method[^\n]*\n.*?^\.end method')
UP={'E()J','K()J','N()J'}; LOW={'s()J','B()J','E()J'}
DELETED={'lgp':UP,'lhk':UP,'aams':LOW,'aamv':LOW}
OLD_M='m(JIZ)J';NEW_M='m(J)J';OLD_H='h(JJLlgw;Z)Lzvi;';NEW_H='h(JJLlgw;)Lzvi;'
LO=-(1<<63);HI=(1<<63)-1

def check(ok,msg):
    if not ok:raise ValueError(msg)
def mmap(t):return {b.splitlines()[0].split()[-1]:b for b in M.findall(t)}
def lines(t):return [l.strip() for l in t.splitlines() if l.strip() and not l.lstrip().startswith(('.line ','#'))]
def code(t):return '\n'.join(lines(t))
def i64(n):return (n+(1<<63))%(1<<64)-(1<<63)
def millis(n):return max(LO,min(HI,n*1000))


def zero_at_calls(body,register,needle,expected_count):
    """Conservative forward analysis, both unknown branch successors and catches.
Any unknown write to the tracked register (or pair overlapping it) kills its
constant. Does not assume successful branch conditions imply local mode.
"""
    c=lines(body);labels={s:i for i,s in enumerate(c) if s.startswith(':')};U='unknown'
    check(not any('switch' in l for l in c),'unexpected switch in caller CFG')
    handlers=[]
    for s in c:
        m=re.fullmatch(r'\.catch(?:all)?(?: \S+)? \{(:\w+) \.\. (:\w+)\} (:\w+)',s)
        if m:handlers.append(tuple(labels[x] for x in m.groups()))
    states={0:U};todo=collections.deque([0]);steps=0
    while todo:
        i=todo.popleft();v=states[i];s=c[i];op=s.split()[0];out=v
        no_dest=s.startswith(('.',':')) or op.startswith(('invoke','iput','sput','aput','if-','goto','return','throw','monitor','check-cast','filled-new-array','fill-array-data'))
        if not no_dest:
            m=re.match(r'\S+ ([vp]\d+)',s);check(m is not None or op=='nop','unrecognized caller instruction '+s)
            if m:
                d=m[1];wide=('wide' in op or (('-long' in op or '-double' in op) and not op.startswith('cmp')))
                if d==register or (wide and d[0]==register[0] and int(d[1:])+1==int(register[1:])):
                    k=re.fullmatch(r'const(?:/4|/16)? '+register+r', (-?0x[0-9a-f]+|-?\d+)',s)
                    out=int(k[1],0) if k else U
        if op.startswith('goto'):successors=[labels[s.split()[-1]]]
        elif op.startswith(('return','throw')):successors=[]
        elif op.startswith('if-'):successors=[i+1,labels[s.split()[-1]]]
        else:successors=[i+1]
        edges=[(x,out) for x in successors if x<len(c)]
        if not s.startswith(('.',':')):edges.extend((h,U) for a,b,h in handlers if a<=i<b)
        for j,value in edges:
            merged=value if j not in states else states[j] if states[j]==value else U
            if j not in states or merged!=states[j]:states[j]=merged;todo.append(j)
        steps+=1;check(steps<100000,'CFG convergence limit')
    targets=[i for i,s in enumerate(c) if needle in s]
    check(len(targets)==expected_count,'caller count')
    for i in targets:check(states.get(i)==0,f'nonlocal or unknown selector {register}: {c[i]}')
    return {'register':register,'calls':len(targets),'zero_proved':True,'analysis_steps':steps}


def supplier_case(body,value):
    c=lines(body);si=next(i for i,s in enumerate(c) if re.fullmatch(r'(packed|sparse)-switch p0, :pswitch_data_\w+',s))
    label=c[si].split()[-1];ti=c.index(label);directive=c[ti+1];mapping={}
    if directive.startswith('.packed-switch'):
        base=int(directive.split()[1],0);end=c.index('.end packed-switch')
        mapping={base+i:x for i,x in enumerate(c[ti+2:end])}
    else:
        end=c.index('.end sparse-switch')
        for s in c[ti+2:end]:
            k,_,v=s.split();mapping[int(k,0)]=v
    start=c.index(mapping[value])+1 if value in mapping else si+1
    out=[]
    for s in c[start:ti]:
        if s.startswith(':') or s=='nop':continue
        out.append(s)
        if s.startswith('return-object'):break
    check(out and out[-1].startswith('return-object'),'supplier result')
    return c[:si],out


class VM:
    """Physical register-index model: p/v aliasing and 64-bit pairs are explicit."""
    def __init__(self, methods, config):self.methods=methods;self.config=config;self.trace=[]
    def execute(self,sig,args):
        body=self.methods[sig];raw=lines(body);n=int(next(x.split()[1] for x in raw if x.startswith('.locals ')))
        c=[x for x in raw if not x.startswith('.')];labels={s:i for i,s in enumerate(c) if s.startswith(':')}
        regs={}
        def idx(s):return int(s[1:])+(n if s.startswith('p') else 0)
        def get(s):
            check(idx(s) in regs,'read uninitialized register '+s+' in '+sig);return regs[idx(s)]
        def put(s,v):regs[idx(s)]=v
        def wide(s):
            lo=get(s);k=idx(s);check(k+1 in regs,'missing high word')
            hi=regs[k+1];check(type(lo)==int and type(hi)==int,'invalid pair '+s)
            return i64((lo&0xffffffff)|((hi&0xffffffff)<<32))
        def putwide(s,v):
            k=idx(s);regs[k]=v&0xffffffff;regs[k+1]=(v>>32)&0xffffffff
        p=0
        for typ,v in args:
            if typ=='J':putwide('p'+str(p),v);p+=2
            else:put('p'+str(p),v);p+=1
        i=0;result=None;steps=0
        while i<len(c):
            s=c[i];op=s.split()[0];steps+=1;check(steps<500,'VM loop')
            if s.startswith(':') or op=='nop':pass
            elif op=='iget-object':
                m=re.fullmatch(r'iget-object (\w+), (\w+), L[^;]+;->(\w+):.*',s);put(m[1],get(m[2])[m[3]])
            elif op in ['iget','iget-wide']:
                m=re.fullmatch(r'\S+ (\w+), (\w+), L[^;]+;->(\w+):.*',s);v=get(m[2])[m[3]]
                if op=='iget-wide':putwide(m[1],v)
                else:put(m[1],v)
            elif op=='sget-object':put(s.split()[1].rstrip(','),'SECONDS')
            elif op.startswith('const-wide'):
                d,v=s.split(' ',1)[1].split(', ');putwide(d,int(v.rstrip('L'),0))
            elif op.startswith('const'):
                d,v=s.split(' ',1)[1].split(', ');put(d,int(v,0))
            elif op.startswith('move-result'):
                if 'wide' in op:putwide(s.split()[1],result)
                else:put(s.split()[1],result)
            elif op.startswith('if-'):
                parts=s.split(' ',1)[1].split(', ');a=get(parts[0]);target=parts[-1]
                if op=='if-eqz':take=(a==0 or a is None)
                elif op=='if-nez':take=(a!=0 and a is not None)
                elif op=='if-ne':take=a!=get(parts[1])
                else:raise ValueError('unmodelled branch '+s)
                if take:i=labels[target];continue
            elif op.startswith('goto'):i=labels[s.split()[-1]];continue
            elif op=='cmp-long':
                d,a,b=s.split(' ',1)[1].split(', ');x,y=wide(a),wide(b);put(d,(x>y)-(x<y))
            elif op=='add-long/2addr':
                d,src=s.split(' ',1)[1].split(', ');putwide(d,i64(wide(d)+wide(src)))
            elif op.startswith('invoke'):
                m=re.fullmatch(r'\S+ \{(.*?)\}, (.+)',s);rs=m[1].split(', ');method=m[2]
                if method.startswith('Llgp;->'):
                    getter=method.split('->')[1];check(get(rs[0]) is self.config,'config receiver changed')
                    result=self.config[getter];self.trace.append(('get',getter))
                elif method=='Ljava/util/concurrent/TimeUnit;->toMillis(J)J':
                    check(get(rs[0])=='SECONDS','wrong time unit');v=wide(rs[1]);result=millis(v);self.trace.append(('millis',v))
                elif method in ['Ljava/lang/Math;->min(JJ)J','Ljava/lang/Math;->max(JJ)J']:
                    x,y=wide(rs[0]),wide(rs[2]);result=min(x,y) if '->min' in method else max(x,y)
                elif method.startswith('Llnk;->m('):
                    callee=method.split('->')[1];ca=[('L',get(rs[0])),('J',wide(rs[1]))]
                    if callee==OLD_M:ca.extend([('I',get(rs[3])),('Z',get(rs[4]))])
                    result=self.execute(callee,ca)
                elif method=='Llcw;->l(I)I':
                    result=get(rs[0]);self.trace.append(('enum',result))
                elif method=='Lzwl;->b(J)Lzvi;':
                    v=wide(rs[0]);result=('timestamp-argument',v);self.trace.append(('timestamp',v))
                else:raise ValueError('unmodelled invoke '+method)
            elif op=='return-wide':return wide(s.split()[1])
            elif op=='return-object':return get(s.split()[1])
            else:raise ValueError('unmodelled instruction '+s)
            i+=1
        raise ValueError('no result')


def arithmetic_tests(bm,am):
    values=[LO,LO+1,LO//1000-1,LO//1000, -100001,-1,0,1,59000,60000,60001,86400000,HI//1000,HI//1000+1,HI-1,HI]
    secs=[LO,-9223372036854776,-1,0,1,60,86400,9223372036854775,9223372036854776,HI]
    mc=0;hc=0
    for lower,upper,request,kind in itertools.product(secs,secs,values,[-1,0,1,2,3,42]):
        config={'O()J':lower,'J()J':upper,'C()J':60,'N()J':999,'K()J':9999,'E()J':0}
        ctx={'c':config};old=VM(bm,config);new=VM(am,config)
        x=old.execute(OLD_M,[('L',ctx),('J',request),('I',kind),('Z',0)])
        y=new.execute(NEW_M,[('L',ctx),('J',request)])
        check(x==y==max(millis(lower),min(millis(upper),request)),'local clamp changed')
        check(old.trace==new.trace,'local config getter order changed');mc+=1
    rng=random.Random(20260912)
    option_kinds=[None,-1,0,1,2,3,42]
    for index in range(4096):
        lower=rng.choice(secs);upper=rng.choice(secs);cap=rng.choice(secs)
        now=rng.choice(values);previous=rng.choice(values);delay=rng.choice(values);kind=rng.choice(option_kinds)
        config={'O()J':lower,'J()J':upper,'C()J':cap,'N()J':123,'K()J':456,'E()J':789}
        ctx={'c':config};options={'k':None if kind is None else {'a':kind,'b':delay}}
        ca=[('L',ctx),('J',now),('J',previous),('L',options)]
        old=VM(bm,config);new=VM(am,config)
        x=old.execute(OLD_H,ca+[('Z',0)]);y=new.execute(NEW_H,ca)
        check(x==y and old.trace==new.trace,'local deadline result/getter order changed');hc+=1
    # Mutation sensitivity: corrupting the lower-bound getter must be detected.
    mutated=dict(am);mutated[NEW_M]=am[NEW_M].replace('Llgp;->O()J','Llgp;->N()J')
    config={'O()J':60,'J()J':86400,'N()J':99};ctx={'c':config}
    check(VM(mutated,config).execute(NEW_M,[('L',ctx),('J',0)])!=VM(am,config).execute(NEW_M,[('L',ctx),('J',0)]),'mutation test insensitive')
    return {'local_clamp_cases':mc,'deadline_register_cases':hc,'mutation_detection':True,
            'external_enum_and_timestamp_helpers':'modelled, not Android execution','seconds_to_millis':'signed saturation','long_addition':'signed 64-bit wrap'}


def verify(before:Path,after:Path):
    b={p.relative_to(before).as_posix():p.read_text() for p in before.glob('smali*/**/*.smali')}
    a={p.relative_to(after).as_posix():p.read_text() for p in after.glob('smali*/**/*.smali')}
    check(a.keys()==b.keys(),'class set changed')
    changed={p for p in b if b[p]!=a[p]}
    expected={f'smali/{c}.smali' for c in ['lnk','lgp','lhk','aams','aamv']}|{f'smali_classes2/{c}.smali' for c in ['lna','lnc','lhh','lhf']}
    check(changed==expected,'edit scope')
    unchanged_methods=0
    for p in changed:
        cls=Path(p).stem;bm,am=mmap(b[p]),mmap(a[p])
        allowed_changes=({'lnk':{NEW_M,NEW_H},'lna':{'a(Ltiz;)Lvox;'},'lnc':{'a(Ltiz;)Lvox;'},'lhh':{'a()Ljava/lang/Object;'},'lhf':{'a()Ljava/lang/Object;'}}).get(cls,set())
        deleted=DELETED.get(cls,set())|({OLD_M,OLD_H} if cls=='lnk' else set())
        added={NEW_M,NEW_H} if cls=='lnk' else set()
        check(set(bm)-set(am)==deleted and set(am)-set(bm)==added,'unexpected method set '+cls)
        for sig in am:
            if sig in allowed_changes:continue
            check(am[sig]==bm[sig],'other method changed '+cls+'->'+sig);unchanged_methods+=1
        norm=lambda t:re.sub(r'\s+',' ',M.sub('',t)).strip()
        check(norm(b[p])==norm(a[p]),'class declaration/field change '+cls)
    # Surrounding caller instructions, constants and all exception regions exact.
    for cls,recv in [('lna','v5'),('lnc','v6')]:
        p=f'smali_classes2/{cls}.smali';t=a[p]
        t=t.replace('invoke-virtual {'+recv+', v8, v9}, Llnk;->'+NEW_M,
                    'invoke-virtual {'+recv+', v8, v9, v3, v7}, Llnk;->'+OLD_M)
        t=t.replace('invoke-virtual/range {v5 .. v10}, Llnk;->'+NEW_H,'invoke-virtual/range {v5 .. v11}, Llnk;->'+OLD_H)
        check(t==b[p],'caller change beyond argument handoff '+cls)
    cfg=[]
    for cls in ['lna','lnc']:
        body=mmap(b[f'smali_classes2/{cls}.smali'])['a(Ltiz;)Lvox;']
        cfg.append(zero_at_calls(body,'v7','Llnk;->'+OLD_M,1))
        if cls=='lna':cfg.append(zero_at_calls(body,'v11','Llnk;->'+OLD_H,2))
    # All surviving supplier cases, including the default 20, stay exact.
    sc=0
    for cls,gone in [('lhh',{6,10}),('lhf',{12})]:
        p=f'smali_classes2/{cls}.smali';sig='a()Ljava/lang/Object;'
        for value in set(range(21))-gone:
            check(supplier_case(mmap(b[p])[sig],value)==supplier_case(mmap(a[p])[sig],value),'supplier changed');sc+=1
    bm=mmap(b['smali/lnk.smali']);am=mmap(a['smali/lnk.smali'])
    arithmetic=arithmetic_tests(bm,am)
    # Config bodies that remain contain no changed flags/defaults (checked above).
    for p,t in a.items():
        for cls,sigs in DELETED.items():check(not any('L'+cls+';->'+sig in t for sig in sigs),'stale config reference')
        check('Llnk;->'+OLD_M not in t and 'Llnk;->'+OLD_H not in t,'stale timing reference')
    count=0
    for p in before.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(before)
        if rel.parts[0].startswith('smali') or rel.parts[0]=='build':continue
        q=after/rel;check(q.is_file() and p.read_bytes()==q.read_bytes(),'non-code payload changed');count+=1
    return {'passed':True,'changed_class_files':sorted(changed),'unchanged_class_files':len(a)-len(changed),
            'retained_methods_in_changed_classes_exact':unchanged_methods,'caller_mode_proofs':cfg,
            'retained_supplier_cases_exact':sc,'arithmetic_and_register_tests':arithmetic,'non_smali_files_compared':count,
            'voice_class_files_unchanged':True,'runtime_tested':False,'privacy_final':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('--json',type=Path);a=p.parse_args()
    result=verify(a.before,a.after);s=json.dumps(result,indent=2)+'\n'
    if a.json:a.json.write_text(s)
    print(s)
if __name__=='__main__':main()
