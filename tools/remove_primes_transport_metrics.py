#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path('/mnt/data/meboard_work/buildtree')

def read(rel): return (ROOT/rel).read_text()
def write(rel,s): (ROOT/rel).write_text(s)
def sub1(s,pat,repl,desc,flags=re.M|re.S):
    ns,n=re.subn(pat,repl,s,count=1,flags=flags)
    if n!=1: raise SystemExit(f'{desc}: expected 1, got {n}')
    return ns

rel=Path('smali_classes3/xra.smali'); s=read(rel)
s=s.replace('.field public final f:Lvpu;\n\n','').replace('.field private final k:Lvpu;\n\n','')
old_sig='.method public constructor <init>(Landroid/content/Context;Llcw;Lxrl;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Lvpu;Lvpu;Lvpu;J)V'
new_sig='.method public constructor <init>(Landroid/content/Context;Llcw;Lxrl;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Lvpu;J)V'
if old_sig not in s: raise SystemExit('xra old ctor signature missing')
s=s.replace(old_sig,new_sig,1)
s=sub1(s,r'(?ms)\n\s*\.line 15.*?iput-object p7, p0, Lxra;->f:Lvpu;\n\n\s*\.line 17.*?iput-object p8, p0, Lxra;->k:Lvpu;\n','\n','xra metric ctor stores')
s=s.replace('iput-object p9, p0, Lxra;->g:Lvpu;','iput-object p7, p0, Lxra;->g:Lvpu;',1)
s=s.replace('iput-wide p10, p0, Lxra;->j:J','iput-wide p8, p0, Lxra;->j:J',1)
for fld in ['f','k']:
    s=sub1(s,rf'(?ms)\n\s*iget-object v1, p0, Lxra;->{fld}:Lvpu;.*?if-eqz v1, :cond_1\n','\n',f'xra equals {fld}')
    s=sub1(s,rf'(?ms)\n\s*iget-object v2, p0, Lxra;->{fld}:Lvpu;.*?xor-int/2addr v0, v2\n','\n',f'xra hash {fld}')
s=sub1(s,r'(?ms)^\.method public final toString\(\)Ljava/lang/String;\n.*?^\.end method','.method public final toString()Ljava/lang/String;\n    .locals 1\n\n    const-string v0, "ChannelConfig"\n    return-object v0\n.end method','xra toString')
write(rel,s)

rel=Path('smali/pwl.smali'); s=read(rel)
s=sub1(s,r'(?ms)\n\s*new-instance v8, Lpch;.*?invoke-direct \{v8, p0\}, Lpch;-><init>\(I\)V\n','\n','pwl Primes provider construction')
s=s.replace('new-instance v10, Lvpx;','new-instance v8, Lvpx;',1)
s=s.replace('invoke-direct {v10, p0}, Lvpx;-><init>(Ljava/lang/Object;)V','invoke-direct {v8, p0}, Lvpx;-><init>(Ljava/lang/Object;)V',1)
s=s.replace('sget-wide v11, Lxrk;->a:J','sget-wide v9, Lxrk;->a:J',1)
s=s.replace('    move-object v9, v8\n\n    .line 107\n    invoke-direct/range {v1 .. v12}, Lxra;-><init>(Landroid/content/Context;Llcw;Lxrl;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Lvpu;Lvpu;Lvpu;J)V','    invoke-direct/range {v1 .. v10}, Lxra;-><init>(Landroid/content/Context;Llcw;Lxrl;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Lvpu;J)V',1)
write(rel,s)

rel=Path('smali_classes3/xrj.smali'); s=read(rel)
s=s.replace('.field public f:Lvpu;\n\n','')
s=sub1(s,r'(?ms)^\.method public final d\(Lvpu;\)V\n.*?^\.end method\n?','', 'xrj metric setter')
write(rel,s)

rel=Path('smali_classes3/xrk.smali'); s=read(rel)
s=s.replace('.field public final f:Lvpu;\n\n','')
old='.method public constructor <init>(Landroid/content/Context;Ljava/net/URI;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Lvpu;Ljava/lang/Integer;Ljava/lang/Integer;JIJJLxsq;)V'
new='.method public constructor <init>(Landroid/content/Context;Ljava/net/URI;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Ljava/lang/Integer;Ljava/lang/Integer;JIJJLxsq;)V'
if old not in s: raise SystemExit('xrk old ctor signature missing')
s=s.replace(old,new,1)
pat=re.compile(rf'(?ms)^{re.escape(new)}\n.*?^\.end method',re.M); m=pat.search(s)
if not m: raise SystemExit('xrk new ctor not found')
ctor='''.method public constructor <init>(Landroid/content/Context;Ljava/net/URI;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Ljava/lang/Integer;Ljava/lang/Integer;JIJJLxsq;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lxrk;->b:Landroid/content/Context;
    iput-object p2, p0, Lxrk;->c:Ljava/net/URI;
    iput-object p3, p0, Lxrk;->m:Ljava/util/concurrent/Executor;
    iput-object p4, p0, Lxrk;->d:Ljava/util/concurrent/Executor;
    iput-object p5, p0, Lxrk;->e:Ljava/util/concurrent/Executor;
    iput-object p6, p0, Lxrk;->g:Ljava/lang/Integer;
    iput-object p7, p0, Lxrk;->h:Ljava/lang/Integer;
    iput-wide p8, p0, Lxrk;->i:J
    iput p10, p0, Lxrk;->j:I
    iput-wide p11, p0, Lxrk;->n:J
    iput-wide p13, p0, Lxrk;->k:J
    move-object/from16 p1, p15
    iput-object p1, p0, Lxrk;->l:Lxsq;
    return-void
.end method'''
s=s[:m.start()]+ctor+s[m.end():]
s=sub1(s,r'(?ms)\n\s*iget-object v1, p0, Lxrk;->f:Lvpu;.*?if-eqz v1, :cond_4\n','\n','xrk equals metric field')
s=sub1(s,r'(?ms)\n\s*iget-object v2, p0, Lxrk;->f:Lvpu;.*?xor-int/2addr v0, v2\n','\n','xrk hash metric field')
s=sub1(s,r'(?ms)^\.method public final toString\(\)Ljava/lang/String;\n.*?^\.end method','.method public final toString()Ljava/lang/String;\n    .locals 1\n\n    const-string v0, "TransportConfig"\n    return-object v0\n.end method','xrk toString')
write(rel,s)

rel=Path('smali_classes3/xrz.smali'); s=read(rel)
s=sub1(s,r'(?ms)\n\s*sget-wide v1, Lxrk;->a:J\n.*?new-instance v2, Lxrj;\n\n\s*\.line 22.*?invoke-direct \{v2\}, Ljava/lang/Object;-><init>\(\)V\n.*?invoke-virtual \{v2, v1\}, Lxrj;->d\(Lvpu;\)V\n','\n    new-instance v2, Lxrj;\n    invoke-direct {v2}, Ljava/lang/Object;-><init>()V\n','xrz default metric provider')
s=sub1(s,r'(?ms)\n\s*iget-object v3, v1, Lxra;->f:Lvpu;\n.*?invoke-virtual \{v2, v3\}, Lxrj;->d\(Lvpu;\)V\n','\n','xrz metric copy')
s=sub1(s,r'(?ms)\n\s*iget-object v11, v2, Lxrj;->f:Lvpu;\n.*?if-eqz v11, :cond_2\n','\n','xrz f required check')
pat=re.compile(r'(?ms)\n\s*:cond_1\n\s*new-instance v5, Lxrk;.*?invoke-direct/range \{v5 \.\. v21\}, Lxrk;-><init>\(Landroid/content/Context;Ljava/net/URI;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Lvpu;Ljava/lang/Integer;Ljava/lang/Integer;JIJJLxsq;\)V'); m=pat.search(s)
if not m: raise SystemExit('xrz xrk construction block not found')
repl='''
    :cond_1
    new-instance v5, Lxrk;
    iget-object v11, v2, Lxrj;->g:Ljava/lang/Integer;
    iget-object v12, v2, Lxrj;->h:Ljava/lang/Integer;
    iget-wide v13, v2, Lxrj;->i:J
    iget v15, v2, Lxrj;->j:I
    iget-wide v3, v2, Lxrj;->k:J
    move-wide/from16 v16, v3
    iget-wide v3, v2, Lxrj;->l:J
    move-wide/from16 v18, v3
    iget-object v3, v2, Lxrj;->m:Lxsq;
    move-object/from16 v20, v3
    invoke-direct/range {v5 .. v20}, Lxrk;-><init>(Landroid/content/Context;Ljava/net/URI;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Ljava/util/concurrent/Executor;Ljava/lang/Integer;Ljava/lang/Integer;JIJJLxsq;)V'''
s=s[:m.start()]+repl+s[m.end():]
s=sub1(s,r'(?ms)\n\s*:cond_7\n\s*iget-object v1, v2, Lxrj;->f:Lvpu;.*?invoke-virtual \{v0, v1\}, Ljava/lang/StringBuilder;->append\(Ljava/lang/String;\)Ljava/lang/StringBuilder;\n','\n    :cond_7\n','xrz missing metric property')
write(rel,s)

rel=Path('smali_classes3/xrc.smali'); s=read(rel)
s=sub1(s,r'(?ms)\n\s*new-array v4, v2, \[Laapv;\n.*?move-result-object v3\n\n\s*\.line 123','\n\n    .line 123','xrc first metric interceptor')
s=sub1(s,r'(?ms)\n\s*new-array v0, v2, \[Laapv;\n.*?move-result-object p0\n\n\s*\.line 336','\n\n    .line 336','xrc second metric interceptor')
write(rel,s)

rel=Path('smali/pch.smali'); s=read(rel)
s=sub1(s,r'(?ms)\n\s*:pswitch_0\n.*?(?=\n\s*:pswitch_2\n)','\n','pch metric cases code')
block=re.search(r'(?ms)(:pswitch_data_0\n\s*\.packed-switch 0x0\n)(.*?)(\s*\.end packed-switch)',s)
if not block: raise SystemExit('pch switch table missing')
lines=[ln for ln in block.group(2).splitlines() if ln.strip()]
if len(lines)!=20 or ':pswitch_1' not in lines[-2] or ':pswitch_0' not in lines[-1]: raise SystemExit('pch metric cases unexpected')
s=s[:block.start(2)]+'\n'.join(lines[:-2])+'\n'+s[block.end(2):]
write(rel,s)

needles=['recordNetworkMetricsToPrimes','recordCachingMetricsToPrimes','Lxrj;->f:Lvpu;','Lxrk;->f:Lvpu;','Lxra;->f:Lvpu;','Lxra;->k:Lvpu;']
for p in ROOT.glob('smali*/**/*.smali'):
    t=p.read_text(errors='ignore')
    for n in needles:
        if n in t: raise SystemExit(f'{n} remains in {p}')
print('Removed Primes network/caching metric callback plumbing and gRPC metric interceptors')
