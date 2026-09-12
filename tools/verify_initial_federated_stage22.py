#!/usr/bin/env python3
"""Independent static/control-flow/argument tests for Stage-22 specialization.
Does not import the patcher. The small interpreters below are NOT an Android VM;
they reject unsupported instructions and validate only the reviewed methods.
"""
from __future__ import annotations
import argparse,collections,itertools,json,re
from pathlib import Path
M=re.compile(r'(?ms)^\.method[^\n]*\n.*?^\.end method')
A='a(Ltiz;)Lvox;';D='d(Llgw;)Lwzc;'
BRANCHES={':cond_0',':cond_5',':cond_24',':cond_35'}
REMOVED_FIELDS={'c','e','l'}

def check(ok,msg):
    if not ok:raise ValueError(msg)
def mmap(t):return {b.splitlines()[0].split()[-1]:b for b in M.findall(t)}
def lines(t):return [l.strip() for l in t.splitlines() if l.strip() and not l.strip().startswith(('.line ','#'))]
def payloads(t):
    out=[]
    for l in lines(t):
        m=re.match(r'\.catch(?:all)?(?: \S+)? \{(:\w+) \.\. (:\w+)\} (:\w+)',l)
        if m:out.append(m.groups())
    return out

def prove_local_worker(body):
    """Forward, conservative single-register constant analysis including catches.
Only the immutable local constructor flag is assumed to be zero. Other tests
explore both successors unless they directly test a proven v7 value.
"""
    c=lines(body);label={s:i for i,s in enumerate(c) if s.startswith(':')}
    catches=[(label[a],label[b],label[h]) for a,b,h in payloads(body)]
    U='unknown';states={0:U};todo=collections.deque([0]);visited=0
    while todo:
        i=todo.popleft();v=states[i];s=c[i];op=s.split()[0];out=v
        if s=='iget-boolean v7, v0, Llna;->c:Z':out=0
        elif not s.startswith(('.',':')) and not op.startswith(('invoke','iput','sput','aput','if-','goto','return','throw','monitor','check-cast','filled-new-array')):
            m=re.match(r'\S+ ([vp]\d+)',s)
            if m:
                dest=m[1];wide=('wide' in op or (('-long' in op or '-double' in op) and not op.startswith('cmp')))
                if dest=='v7' or (wide and dest=='v6'):
                    k=re.match(r'const(?:/4|/16)? v7, (-?0x[0-9a-f]+|-?\d+)',s)
                    out=int(k[1],0) if k else U
        if op.startswith('goto'):succ=[label[s.split()[-1]]]
        elif op.startswith('return') or op=='throw':succ=[]
        elif op.startswith('if-'):
            target=label[s.split()[-1]];succ=[i+1,target]
            if re.match(r'if-(?:eqz|nez) v7,',s) and v!=U:
                jump=(v==0) if op=='if-eqz' else (v!=0)
                succ=[target] if jump else [i+1]
        else:succ=[i+1]
        edges=[(j,out) for j in succ if j<len(c)]
        # Conservatively include exceptional edges for every real instruction
        # inside a protected range. Catch handlers terminate in this worker.
        if not s.startswith(('.',':')):
            edges += [(h,U) for a,b,h in catches if a<=i<b]
        for j,value in edges:
            merged=value if j not in states else (states[j] if states[j]==value else U)
            if j not in states or states[j]!=merged:states[j]=merged;todo.append(j)
        visited+=1;check(visited<100000,'analysis did not converge')
    intervals=[]
    for target in BRANCHES:
        instruction='if-eqz v7, '+target
        check(c.count(instruction)==1,'missing worker discriminator')
        start=c.index(instruction);end=label[target]
        check(states.get(start)==0,'local flag not proven zero at '+target)
        check(all(i not in states for i in range(start+1,end)), 'removed region reachable for local input '+target)
        intervals.append((start,end))
    keep=[s for i,s in enumerate(c) if not any(a<=i<b for a,b in intervals)]
    keep.remove('iget-boolean v7, v0, Llna;->c:Z')
    call='invoke-virtual {v5, v8, v9, v3, v7}, Llnk;->m(JIZ)J'
    keep.insert(keep.index(call),'const/4 v7, 0x0')
    return keep,{'proven_local_only_branch_regions':4,'unreachable_instruction_and_directive_lines':sum(b-a-1 for a,b in intervals),'analysis_steps':visited}

def constructor_fields(body,arguments):
    regs={'p0':'worker'};regs.update({f'p{i}':x for i,x in enumerate(arguments,1)})
    out={}
    for s in lines(body):
        m=re.match(r'iput(?:-object|-wide)? (p\d+), p0, Llna;->(\w+):',s)
        b=re.match(r'iput-boolean (p\d+), p0, Llna;->(\w+):',s)
        if m or b:
            m=m or b;check(m[1] in regs,'missing constructor argument');out[m[2]]=regs[m[1]]
    return out

class MiniError(Exception):pass

def run_entry(body,ctor,opts):
    """Execute only the reviewed Java-side argument preparation and monitor flow."""
    c=lines(body);labels={l:i for i,l in enumerate(c) if l.startswith(':')}
    catches=[(labels[a],labels[b],labels[h]) for a,b,h in payloads(body)]
    r={'p0':{'kind':'scheduler','b':{'kind':'context'},'d':'metrics'},'p1':opts}
    result=None;exception=None;depth=0;events=[];i=0;steps=0
    def setreg(reg,v,wide=False):
        r[reg]=v
        if wide:r[reg[0]+str(int(reg[1:])+1)]=('high',v)
    while i<len(c):
        s=c[i];op=s.split()[0];steps+=1;check(steps<1000,'entry loop')
        try:
            if s.startswith(('.',':')):pass
            elif op.startswith('move-result'):setreg(s.split()[1],result,'wide' in op)
            elif op=='move-exception':setreg(s.split()[1],exception)
            elif op.startswith('move'):
                d,src=s.split(' ',1)[1].split(', ');setreg(d,r[src],'wide' in op)
            elif op.startswith('const-string'):
                d,src=s.split(' ',1)[1].split(', ',1);setreg(d,json.loads(src))
            elif op.startswith('const'):
                d,src=s.split(' ',1)[1].split(', ');setreg(d,int(src,0),'wide' in op)
            elif op.startswith('iget'):
                m=re.fullmatch(r'\S+ (\w+), (\w+), L[^;]+;->(\w+):.+',s)
                check(m is not None,'iget parse');setreg(m[1],r[m[2]][m[3]],'wide' in op)
            elif op.startswith('sget-object'):
                d,src=s.split(' ',1)[1].split(', ');setreg(d,src)
            elif op=='cmp-long':
                d,x,y=s.split(' ',1)[1].split(', ');setreg(d,(r[x]>r[y])-(r[x]<r[y]))
            elif op=='new-instance':
                d,typ=s.split(' ',1)[1].split(', ');setreg(d,{'kind':typ,'text':''})
            elif op=='monitor-enter':depth+=1
            elif op=='monitor-exit':depth-=1;check(depth>=0,'negative monitor depth')
            elif op.startswith('goto'):i=labels[s.split()[-1]];continue
            elif op.startswith('if-'):
                args=s.split(' ',1)[1].split(', ');x=r[args[0]];cond=op[3:]
                zero=x is None or x==0
                take={'eqz':zero,'nez':not zero,'lez':isinstance(x,(int,float)) and x<=0}.get(cond)
                check(take is not None,'unsupported entry branch '+s)
                if take:i=labels[args[-1]];continue
            elif op.startswith('invoke'):
                m=re.fullmatch(r'\S+ \{(.*?)\}, (.+)',s);check(m is not None,'invoke parse')
                spec,method=m.groups()
                if ' .. ' in spec:
                    start,end=spec.split(' .. ');args=[r[start[0]+str(j)] for j in range(int(start[1:]),int(end[1:])+1)]
                else:args=[r[x] for x in spec.split(', ')] if spec else []
                if method=='Landroid/content/Context;->getPackageName()Ljava/lang/String;':result='com.mekromn.meboard'
                elif method=='Ljava/lang/StringBuilder;-><init>()V':pass
                elif method.startswith('Ljava/lang/StringBuilder;->append'):
                    args[0]['text']+=str(args[1]);result=args[0]
                elif method=='Ljava/lang/StringBuilder;->toString()Ljava/lang/String;':result=args[0]['text']
                elif method.startswith('Lunb;->bk('):result=('namespace',*args);events.append(('namespace',*args))
                elif method.startswith('Llcw;->g('):result=('unused_tir',args[0])
                elif method.startswith('Llcw;->k('):result=list(args[0] or [])
                elif method.startswith('Ljava/util/List;->isEmpty'):result=int(not args[0])
                elif method.startswith('Llgy;->e('):events.append(('metric',args[1]))
                elif method.startswith('Llna;-><init>'):
                    fields=constructor_fields(ctor,args[1:]);args[0]['fields']=fields
                    result=None
                elif method.startswith('Llnk;->v('):
                    check('fields' in args[1],'worker not constructed')
                    fields={k:v for k,v in args[1]['fields'].items() if k not in REMOVED_FIELDS}
                    events.append(('submit',fields));result=('future',fields)
                elif method.startswith(('Ljava/lang/IllegalArgumentException;-><init>', 'Ljava/lang/UnsupportedOperationException;-><init>')):
                    if len(args)>1:args[0]['text']=args[1]
                else:raise ValueError('unsupported entry invoke '+method)
            elif op=='return-object':return {'result':'returned','value':r[s.split()[1]],'events':events,'monitor_depth':depth}
            elif op=='throw':raise MiniError(r[s.split()[1]])
            else:raise ValueError('unsupported entry instruction '+s)
        except MiniError as exc:
            exception=exc.args[0];handlers=[h for a,b,h in catches if a<=i<b]
            if handlers:i=handlers[0];continue
            return {'result':'threw','type':exception['kind'],'events':events,'monitor_depth':depth}
        i+=1
    raise ValueError('entry did not return')

def verify(before:Path,after:Path):
    b={p.relative_to(before).as_posix():p.read_text() for p in before.glob('smali*/**/*.smali')}
    a={p.relative_to(after).as_posix():p.read_text() for p in after.glob('smali*/**/*.smali')}
    check(a.keys()==b.keys(),'class set changed')
    changed={p for p in a if a[p]!=b[p]};check(changed=={'smali/lnk.smali','smali/lcw.smali','smali_classes2/lna.smali'},'edit scope')
    retained=0
    for p in changed:
        bm=mmap(b[p]);am=mmap(a[p]);cls=Path(p).stem
        if cls=='lcw':check(set(bm)-set(am)=={'g(I)Ltir;','h(Llgw;)Ltis;'} and not set(am)-set(bm),'removed helper methods')
        elif cls=='lnk':check(bm.keys()==am.keys(),'scheduler API changed')
        else:check(len(set(bm)-set(am))==1 and len(set(am)-set(bm))==1,'constructor-only method migration')
        for sig in am:
            if (cls=='lnk' and sig==D) or (cls=='lna' and (sig==A or sig.startswith('<init>'))):continue
            check(sig in bm and bm[sig]==am[sig],'other method changed '+cls+'->'+sig);retained+=1
        old_out=M.sub('',b[p]);new_out=M.sub('',a[p])
        if cls=='lna':old_out=re.sub(r'(?m)^\.field public final synthetic (?:c:Z|e:Ljava/lang/String;|l:Ltir;)\n','',old_out)
        check(re.sub(r'\s+',' ',old_out).strip()==re.sub(r'\s+',' ',new_out).strip(),'unexpected declaration/field edit')
    old_worker=mmap(b['smali_classes2/lna.smali']);new_worker=mmap(a['smali_classes2/lna.smali'])
    projected,proof=prove_local_worker(old_worker[A])
    check(projected==lines(new_worker[A]),'retained worker body differs from proved local projection')
    entry_before=mmap(b['smali/lnk.smali'])[D];entry_after=mmap(a['smali/lnk.smali'])[D]
    old_ctor=next(v for k,v in old_worker.items() if k.startswith('<init>'))
    new_ctor=next(v for k,v in new_worker.items() if k.startswith('<init>'))
    cases=0;accepted=0;rejected=0
    for name,job,delay,j,l,bundle in itertools.product(['learn','日本語'],[1,9001],[-1,0,1,2**40],[None,'model_uri'],[None,'output_uri'],[[],['one']]):
        options={'b':name,'c':job,'e':None,'f':3,'g':'input_uri','j':j,'l':l,'m':bundle,'i':delay}
        x=run_entry(entry_before,old_ctor,options);y=run_entry(entry_after,new_ctor,options)
        check(x==y,'local entry behavior changed: '+str(options));check(y['monitor_depth']==0,'monitor leak')
        cases+=1;accepted+=int(y['result']=='returned');rejected+=int(y['result']=='threw')
    for population in ['federated_population','']:
        options={'b':'test','c':1,'e':population,'f':1,'g':None,'j':None,'l':None,'m':[],'i':0}
        y=run_entry(entry_after,new_ctor,options)
        check(y['result']=='threw' and y['type']=='Ljava/lang/UnsupportedOperationException;' and not y['events'] and y['monitor_depth']==0,'nonlocal request not rejected before work')
    old_tail=entry_before[entry_before.index('    :try_end_0'):];new_tail=entry_after[entry_after.index('    :try_end_0'):]
    check(old_tail==new_tail,'monitor cleanup changed')
    # Native and other payload files remain exact in the decoded trees.
    count=0
    for p in before.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(before)
        if rel.parts[0].startswith('smali') or rel.parts[0]=='build':continue
        q=after/rel;check(q.is_file() and p.read_bytes()==q.read_bytes(),'non-code change '+str(rel));count+=1
    return {'passed':True,'unchanged_class_files':len(a)-3,'other_methods_byte_identical':retained,
      'local_entry_cases_compared':cases,'valid_local_cases':accepted,'invalid_local_cases_same_rejection':rejected,
      'nonlocal_inputs_rejected_before_work':2,'local_worker_control_flow_proof':proof,
      'non_smali_files_compared':count,'local_rescheduler_and_interval_helpers_unchanged':True,
      'runtime_tested':False,'test_scope':'static CFG and limited entry/constructor symbolic interpreter, not Android execution'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('--json',type=Path)
    a=p.parse_args();s=json.dumps(verify(a.before,a.after),indent=2)+'\n'
    if a.json:a.json.write_text(s)
    print(s)
if __name__=='__main__':main()
