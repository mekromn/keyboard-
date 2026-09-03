#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path('/mnt/data/meboard_work/buildtree')

def find(cls):
    hits=list(ROOT.glob(f'smali*/**/{cls}.smali'))
    if len(hits)!=1: raise SystemExit(f'{cls}: expected one file, got {hits}')
    return hits[0]

def methods(text):
    out=[];pos=0
    while True:
        m=re.search(r'^\.method[^\n]*\n',text[pos:],re.M)
        if not m: break
        a=pos+m.start(); b=text.find('\n.end method',pos+m.end())
        if b<0: raise SystemExit('unterminated method')
        b += len('\n.end method')
        out.append((a,b,text[a:b])); pos=b
    return out

def prune_switch_method(body, case):
    # Support the single packed switch used by these synthetic dispatchers.
    dm=re.search(r'(?ms)(^\s*:pswitch_data_[0-9a-f]+\s*\n\s*\.packed-switch\s+0x([0-9a-f]+)\s*\n)(.*?)(^\s*\.end packed-switch)',body,re.M)
    if not dm:return body,0
    base=int(dm.group(2),16); labels=re.findall(r':pswitch_[0-9a-f]+',dm.group(3)); cmap={base+i:l for i,l in enumerate(labels)}
    if case not in cmap:return body,0
    lab=cmap[case]
    # Only remove if the branch exists in code before switch data.
    data_pos=dm.start()
    ms=list(re.finditer(rf'(?m)^\s*{re.escape(lab)}\s*$',body[:data_pos]))
    if not ms:return body,0
    # Point impossible discriminator at an adjacent retained branch; its producer is removed too.
    keep=[c for c in cmap if c!=case]
    repl=cmap[min(keep,key=lambda c:abs(c-case))]
    data=dm.group(3)
    data,n=re.subn(rf'(?m)^(\s*){re.escape(lab)}\s*$',rf'\1{repl}',data,count=1)
    if n!=1:raise SystemExit(f'failed switch table rewrite case {case}')
    body=body[:dm.start(3)]+data+body[dm.end(3):]
    data_pos=body.rfind(':pswitch_data_')
    ms=list(re.finditer(rf'(?m)^\s*{re.escape(lab)}\s*$',body[:data_pos])); st=ms[-1].start()
    nxt=re.search(r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',body[ms[-1].end():data_pos]); en=ms[-1].end()+nxt.start() if nxt else data_pos
    # Preserve any internal label that is targeted from retained code outside the removed branch.
    seg=body[st:en]; preserve=en; outside=body[:st]+body[en:data_pos]
    for lm in re.finditer(r'(?m)^\s*(:[A-Za-z0-9_]+)\s*$',seg):
        l2=lm.group(1)
        if l2.startswith(':pswitch_'):continue
        if re.search(rf'(?<![A-Za-z0-9_]){re.escape(l2)}(?![A-Za-z0-9_])',outside): preserve=min(preserve,st+lm.start())
    body=body[:st]+body[preserve:]
    return body,1

def prune_class_cases(cls,case,min_methods=1):
    p=find(cls);t=p.read_text(); changed=0
    for a,b,body in reversed(methods(t)):
        nb,n=prune_switch_method(body,case)
        if n:
            t=t[:a]+nb+t[b:];changed+=n
    if changed<min_methods:raise SystemExit(f'{cls}: expected >= {min_methods} methods with case {case}, got {changed}')
    p.write_text(t);print(f'{cls}: physically removed discriminator case {case} from {changed} method(s)')

def remove_method(cls, signature_regex, desc):
    p=find(cls);t=p.read_text(); pat=re.compile(rf'(?ms)^\.method[^\n]*{signature_regex}\n.*?^\.end method\n?')
    t,n=pat.subn('',t,count=1)
    if n!=1:raise SystemExit(f'{cls}: {desc} not uniquely found')
    p.write_text(t);print(f'{cls}: removed {desc}')

# 1) Remove the actual Phenotype module factory entry from the compacted application module registry.
eq=find('eqt'); lines=eq.read_text().splitlines()
mi=next(i for i,l in enumerate(lines) if l.startswith('.method public final aI()Ljava/util/Set;'))
me=next(i for i in range(mi+1,len(lines)) if lines[i]=='.end method')
method=lines[mi:me+1]
arr_i=next(i for i,l in enumerate(method) if 'new-array v11, v11, [Lpth;' in l)
# Determine all current aput stores and their construction blocks.
aputs=[i for i in range(arr_i+1,len(method)) if re.match(r'\s*aput-object\s+\w+,\s+v11,\s+\w+',method[i])]
if len(aputs)!=246:raise SystemExit(f'expected 246 registry entries, got {len(aputs)}')
slot=149; end=aputs[slot]; prev=arr_i if slot==0 else aputs[slot-1]
start=None
for k in range(prev+1,end+1):
    if re.match(r'\s*new-instance\s+',method[k]): start=k;break
if start is None:raise SystemExit('Phenotype registry block start missing')
block='\n'.join(method[start:end+1])
if 'Lpks;' not in block or '<init>(I)V' not in block:raise SystemExit('registry slot 149 is not expected pks factory')
# Assert this exact slot is pks discriminator 11 using lightweight register-constant tracking.
regs={}
disc=None
for line in method[:end+1]:
    s=line.strip()
    m=re.match(r'const(?:/4|/16)?\s+(v\d+),\s+(-?0x[0-9a-f]+|-?\d+)',s)
    if m: regs[m.group(1)]=int(m.group(2),0); continue
    m=re.match(r'move(?:/from16|/16)?\s+(v\d+),\s+(v\d+)',s)
    if m: regs[m.group(1)]=regs.get(m.group(2)); continue
    m=re.match(r'invoke-direct \{v4,\s*(v\d+)\}, Lpks;-><init>\(I\)V',s)
    if m and line in method[start:end+1]: disc=regs.get(m.group(1))
if disc!=11:raise SystemExit(f'registry slot 149 expected pks discriminator 11, got {disc}')
del method[start:end+1]
# Reduce array length constant 0xf6 -> 0xf5.
for j in range(max(0,arr_i-8),arr_i):
    if re.search(r'const/16 v11, 0xf6\b',method[j]):method[j]='    const/16 v11, 0xf5';break
else:raise SystemExit('registry size constant 0xf6 not found')
# Re-index every array store sequentially using v23.
aputs=[i for i in range(arr_i+1,len(method)) if re.match(r'\s*aput-object\s+(\w+),\s+v11,\s+\w+',method[i])]
offset=0
for idx,pos0 in enumerate(aputs):
    pos=pos0+offset;m=re.match(r'(\s*)aput-object\s+(\w+),\s+v11,\s+\w+',method[pos]);indent,obj=m.groups()
    method[pos:pos+1]=[f'{indent}const/16 v23, 0x{idx:x}',f'{indent}aput-object {obj}, v11, v23'];offset+=1
lines[mi:me+1]=method;eq.write_text('\n'.join(lines)+'\n')
print('eqt: removed Phenotype module registry slot 149; registry now 245 entries')

# 2) Delete every shared synthetic branch used by that module.
prune_class_cases('pks',11,2)
prune_class_cases('pdm',14,1)
prune_class_cases('pvh',9,1)
prune_class_cases('pld',3,1)
prune_class_cases('fvz',8,2)
prune_class_cases('fqg',15,2)

# 3) Delete constructors that can only construct Phenotype callbacks.
remove_method('fvz',r'constructor <init>\(Lqdp;Lqdg;I\)V','Phenotype callback constructor')
remove_method('fqg',r'constructor <init>\(Lqdp;I\)V','Phenotype callback constructor')
remove_method('qdl',r'constructor <init>\(Lqdp;Llsz;Lwzf;Lqdg;I\)V','Phenotype async bridge constructor')

# 4) qdl is shared. Physically delete its discriminator-0 Phenotype branch, retaining only generic async work.
p=find('qdl');t=p.read_text();m=re.search(r'(?ms)^\.method public final a\(Lbbj;\)Ljava/lang/Object;\n.*?^\.end method',t,re.M)
if not m:raise SystemExit('qdl a(Lbbj) missing')
b=m.group(0)
# Drop field test and jump; retained path begins with old .line 4.
pre=re.search(r'(?ms)(^\.method[^\n]*\n\s*\.locals\s+\d+\s*\n).*?\s*\.line 4\s*\n',b,re.M)
if not pre or ':cond_0' not in b:raise SystemExit('qdl discriminator layout unexpected')
ret_start=pre.end()
cond=b.find('\n    :cond_0',ret_start)
if cond<0:raise SystemExit('qdl Phenotype cond_0 missing')
ret=b[ret_start:cond]
# retained branch must already return before phenotype branch
if 'return-object' not in ret:raise SystemExit('qdl retained path missing return')
newb=pre.group(1)+'\n    .line 4\n'+ret.strip('\n')+'\n.end method'
t=t[:m.start()]+newb+t[m.end():];p.write_text(t)
print('qdl: removed discriminator-0 Phenotype branch')

# 5) Backup should never trigger remote flag fetching. Remove the private fetch method and its two call sites.
p=find('com/google/android/libraries/inputmethod/backup/BackupAgent');t=p.read_text()
pat=re.compile(r'(?ms)^\.method private final g\(\)V\n.*?^\.end method\n?');t,n=pat.subn('',t,count=1)
if n!=1:raise SystemExit('BackupAgent g() remote fetch method missing')
t,n=re.subn(r'(?m)^\s*invoke-direct \{v1\}, Lcom/google/android/libraries/inputmethod/backup/BackupAgent;->g\(\)V\n','',t)
# Second call may use p0/v1 depending method register allocation.
t,n2=re.subn(r'(?m)^\s*invoke-direct \{p0\}, Lcom/google/android/libraries/inputmethod/backup/BackupAgent;->g\(\)V\n','',t)
if n+n2!=2:raise SystemExit(f'expected two BackupAgent g() callsites, removed {n+n2}')
p.write_text(t);print('BackupAgent: removed forced remote Phenotype refresh method and 2 callsites')

# 6) Delete dedicated remote Phenotype implementation cluster after all shared branches are gone.
DELETE=['qdp','qdf','qde','qdg','qdh','qdj','qdi','qdk','qdm','qdn','qdo']
classes={}
for f in ROOT.glob('smali*/**/*.smali'):
    tx=f.read_text(errors='ignore');mm=re.search(r'^\.class[^\n]* L([^;]+);',tx,re.M)
    if mm:classes[mm.group(1)]=(f,tx)
D=set(DELETE)
for c in DELETE:
    if c not in classes:raise SystemExit(f'{c} missing before deletion')
    ext=[x for x,(_,tx) in classes.items() if x not in D and f'L{c};' in tx]
    if ext:raise SystemExit(f'{c} still externally referenced by {ext[:20]}')
for c in DELETE:
    classes[c][0].unlink();print('deleted',c)
print('remote Phenotype fetch/update module physically removed; bundled/static flag code retained')
