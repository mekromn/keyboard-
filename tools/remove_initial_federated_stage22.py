#!/usr/bin/env python3
"""Physically remove federated initial-registration branches from pinned Stage 21.
The public entry rejects nonlocal requests. Local creation, update and cleanup
remain; historical-record parsing is not deleted. No no-op classes are added.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
INPUT_SHA='c83284fd77f0a99667f39530441ee10391cf185add1cc6e1d64378ba59b41d0e'
EXPECTED = {'smali/lnk.smali': '190a4135d8b3f823898fd6f43905cc82b2cbfdfcf954003fb1bc05dd16d8a075', 'smali/lcw.smali': '95e0a4915dfa429d6429c7ebf26ef4ba29e8f541779ccef258f238cefb4c4440', 'smali_classes2/lna.smali': '43060b48e45a99feda50fa6ea2a5c4d118def9d9fc7794706f5f154eb987ac2a', 'smali/lgw.smali': 'f9d61518e1b94fc023911db72f564309fc0b56670145fb2360847c2fe8c5190d'}
METHOD=re.compile(r'(?ms)^\.method[^\n]*\n.*?^\.end method')
OLD_CTOR='<init>(Llnk;Ljava/lang/String;ZILjava/lang/String;Landroid/net/Uri;Landroid/net/Uri;Landroid/net/Uri;Ljava/util/List;Llgw;Ljava/lang/String;Ltir;J)V'
NEW_CTOR='<init>(Llnk;Ljava/lang/String;ILandroid/net/Uri;Landroid/net/Uri;Landroid/net/Uri;Ljava/util/List;Llgw;Ljava/lang/String;J)V'
SCHEDULE='d(Llgw;)Lwzc;'
ACTION='a(Ltiz;)Lvox;'
REMOVED_STATIC={'g(I)Ltir;','h(Llgw;)Ltis;'}
BRANCHES=['cond_0','cond_5','cond_24','cond_35']


def check(ok,msg):
    if not ok:raise ValueError(msg)

def digest(t):return hashlib.sha256(t.encode()).hexdigest()
def methods(t):return {m.splitlines()[0].split()[-1]:m for m in METHOD.findall(t)}
def locate(t,line):
    m=re.search(r'(?m)^[ \t]*'+re.escape(line)+r'[ \t]*$',t)
    check(m is not None,'missing exact line '+line)
    return m.start()
def cut(t,start,end,replacement=''):
    a=locate(t,start);b=locate(t,end)
    check(a<b,'reversed block '+start)
    return t[:a]+replacement+t[b:]
def once(t,old,new):
    check(t.count(old)==1,'expected one occurrence: '+old)
    return t.replace(old,new,1)
def validate_labels(t):
    for body in methods(t).values():
        body=re.sub(r'"(?:\\.|[^"\\])*"','""',body)
        body=re.sub(r'(?m)#.*$','',body)
        declarations=re.sub(r'(?ms)^[ \t]*\.(packed-switch|sparse-switch|array-data)\b.*?^[ \t]*\.end \1[^\n]*', '', body)
        declared=re.findall(r'(?m)^\s*(:\w+)\s*$',declarations)
        check(len(declared)==len(set(declared)),'duplicate label')
        targets=set(re.findall(r'(?<![\w]):(?:cond|goto|try_start|try_end|catch|catchall|pswitch|sswitch|array)_[\w]+',body))
        check(targets<=set(declared),'unresolved label '+str(targets-set(declared)))


def apply(root:Path,report:Path,dry_run=False):
    before={p.relative_to(root).as_posix():p.read_text() for p in root.glob('smali*/**/*.smali')}
    check(len(before)==21761,'wrong class count')
    for p,h in EXPECTED.items():check(p in before and digest(before[p])==h,'input drift: '+p)
    check({p for p,t in before.items() if 'Llna;->' in t}=={'smali/lnk.smali','smali_classes2/lna.smali'},'new helper access')
    for sig,expected in [('h(Llgw;)Ltis;',{'smali_classes2/lna.smali'}),('g(I)Ltir;',{'smali/lnk.smali','smali/lcw.smali'})]:
        check({p for p,t in before.items() if 'Llcw;->'+sig in t}==expected,'new static helper consumer')
    check(not any(re.search(r'const-string(?:/jumbo)?[^\n]*"(?:lna|lnk|lcw|Llna;|Llnk;|Llcw;)"',t) for t in before.values()),'reflective literal requires review')
    after=dict(before)
    # Reject a non-null federated population before any state/job registration.
    text=before['smali/lnk.smali'];old=methods(text)[SCHEDULE]
    guard='''    iget-object v0, v10, Llgw;->e:Ljava/lang/String;
    if-eqz v0, :cond_local_only
    new-instance v0, Ljava/lang/UnsupportedOperationException;
    const-string v1, "FEDERATED_TRAINING_OPTIONS"
    invoke-direct {v0, v1}, Ljava/lang/UnsupportedOperationException;-><init>(Ljava/lang/String;)V
    throw v0
    :cond_local_only
'''
    new=once(old,'    :try_start_0\n','    :try_start_0\n'+guard)
    # The local namespace already used an empty suffix. Delete only the
    # federated population selection and now-unused metadata conversion.
    new=cut(new,'iget-object v5, v10, Llgw;->e:Ljava/lang/String;',
        'iget-object v6, v10, Llgw;->g:Landroid/net/Uri;',
        '    const-string v1, ""\n    invoke-static {v0, v1}, Lunb;->bk(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;\n    move-result-object v11\n\n')
    new=cut(new,'if-eqz v5, :cond_2','if-eqz v7, :cond_3')
    shuffle='''    move v3, v4
    move-object v4, v6
    move-object v5, v7
    move-object v6, v8
    move-object v7, v9
    move-object v8, v10
    move-object v9, v11
    move-wide v10, v13
    invoke-direct/range {v0 .. v11}, Llna;->'''+NEW_CTOR
    new=once(new,'    invoke-direct/range {v0 .. v14}, Llna;->'+OLD_CTOR,shuffle)
    after['smali/lnk.smali']=once(text,old,new)
    # Specialize the existing worker to local jobs. Each removed fallthrough
    # region is guarded by the immutable constructor flag derived above.
    text=before['smali_classes2/lna.smali'];old=methods(text)[ACTION];new=old
    for label in BRANCHES:new=cut(new,'if-eqz v7, :'+label,':'+label)
    new=once(new,'    iget-boolean v7, v0, Llna;->c:Z\n','')
    # The remaining call uses the existing shared local interval helper. This
    # argument is its local-mode selector, not a retained telemetry enable flag.
    call='    invoke-virtual {v5, v8, v9, v3, v7}, Llnk;->m(JIZ)J'
    new=once(new,call,'    const/4 v7, 0x0\n'+call)
    text=once(text,old,new)
    for declaration in ['.field public final synthetic c:Z','.field public final synthetic e:Ljava/lang/String;','.field public final synthetic l:Ltir;']:
        text=once(text,declaration+'\n','')
    ctor=''' .method public synthetic constructor '''+NEW_CTOR+'''
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Llna;->a:Llnk;
    iput-object p2, p0, Llna;->b:Ljava/lang/String;
    iput p3, p0, Llna;->d:I
    iput-object p4, p0, Llna;->f:Landroid/net/Uri;
    iput-object p5, p0, Llna;->g:Landroid/net/Uri;
    iput-object p6, p0, Llna;->h:Landroid/net/Uri;
    iput-object p7, p0, Llna;->i:Ljava/util/List;
    iput-object p8, p0, Llna;->j:Llgw;
    iput-object p9, p0, Llna;->k:Ljava/lang/String;
    iput-wide p10, p0, Llna;->m:J
    return-void
.end method'''
    text=once(text,methods(text)[OLD_CTOR],ctor.lstrip())
    after['smali_classes2/lna.smali']=text
    # The federated options serializer and its enum converter have no callers
    # after the branch removal. Delete the method bodies, not their classes.
    text=before['smali/lcw.smali'];mm=methods(text)
    for sig in REMOVED_STATIC:text=once(text,mm[sig],'')
    after['smali/lcw.smali']=text
    changed=sorted(p for p in after if before[p]!=after[p])
    check(set(changed)=={'smali/lcw.smali','smali/lnk.smali','smali_classes2/lna.smali'},'unexpected scope')
    forbidden=['Llna;->'+OLD_CTOR,'Llna;->c:Z','Llna;->e:Ljava/lang/String;','Llna;->l:Ltir;']+['Llcw;->'+s for s in REMOVED_STATIC]
    for p,t in after.items():check(not any(n in t for n in forbidden),'stale member reference '+p)
    for p in changed:validate_labels(after[p])
    result={'input_apk_sha256':INPUT_SHA,'classes_before':len(before),'classes_after':len(after),
      'modified_files':changed,'untouched_class_files':len(after)-len(changed),'deleted_classes':[],
      'deleted_static_methods':sorted(REMOVED_STATIC),'deleted_worker_fields':['c:Z','e:Ljava/lang/String;','l:Ltir;'],
      'worker_constructor_before':OLD_CTOR,'worker_constructor_after':NEW_CTOR,
      'federated_branch_regions_deleted':len(BRANCHES),'public_entry_signature_unchanged':True,
      'unsupported_input':'non-null federated population throws UnsupportedOperationException',
      'net_smali_bytes_removed':sum(len(before[p].encode())-len(after[p].encode()) for p in changed),
      'before_hashes':{p:digest(before[p]) for p in changed},'after_hashes':{p:digest(after[p]) for p in changed},
      'native_changed':False,'runtime_tested':False,'privacy_final':False,'dry_run':dry_run}
    if not dry_run:
        for p in changed:(root/p).write_text(after[p])
    report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(result,indent=2)+'\n')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--report',type=Path,required=True);p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    print(json.dumps(apply(a.root,a.report,a.dry_run),indent=2))
if __name__=='__main__':main()
