from pathlib import Path
import re
R=Path('/mnt/data/meboard_work/buildtree')
def sub1(s,pat,repl,d,flags=re.M|re.S):
 o,n=re.subn(pat,repl,s,count=1,flags=flags)
 if n!=1: raise SystemExit(f'{d}: {n}')
 return o
# ffw Apostrophe promo
p=R/'smali/ffw.smali';s=p.read_text();s=s.replace('.field private final g:Lpqq;\n','').replace('.field private j:Lfga;\n','');s=s.replace('.method public constructor <init>(Lpqu;Lpqq;)V','.method public constructor <init>(Lpqu;)V',1);s=sub1(s,r'(?m)^\s*iput-object p2, p0, Lffw;->g:Lpqq;\n','', 'ffw ctor logger')
s=sub1(s,r'(?ms)\s*new-instance p1, Lfga;.*?invoke-interface \{p0, p1\}, Lpqu;->a\(Lpqt;\)Lpqu;\n','\n','ffw register metrics')
s=sub1(s,r'(?ms)\s*iget-object v0, p0, Lffw;->j:Lfga;.*?iput-object v0, p0, Lffw;->j:Lfga;\n','\n','ffw unregister metrics');p.write_text(s)
# fjz Clipboard
p=R/'smali/fjz.smali';s=p.read_text();s=s.replace('.field private final j:Lpqq;\n','').replace('.field private k:Lpqw;\n','');s=s.replace('.method public constructor <init>(Lpqu;Lpqq;)V','.method public constructor <init>(Lpqu;)V',1);s=sub1(s,r'(?m)^\s*iput-object p2, p0, Lfjz;->j:Lpqq;\n','', 'fjz ctor logger')
# p2 ceased to exist when the logger parameter was removed. Move the retained
# Clipboard facilitator temporary into local v0 rather than leaving an invalid
# parameter-register reference that ART rejects when the class is loaded.
s=sub1(s,r'new-instance p2, Lfjv;','new-instance v0, Lfjv;','fjz retained facilitator allocation',flags=re.M)
s=sub1(s,r'invoke-direct \{p2, p1\}, Lfjv;-><init>\(Lpqu;\)V','invoke-direct {v0, p1}, Lfjv;-><init>(Lpqu;)V','fjz retained facilitator init',flags=re.M)
s=sub1(s,r'iput-object p2, p0, Lfjz;->f:Lfjv;','iput-object v0, p0, Lfjz;->f:Lfjv;','fjz retained facilitator store',flags=re.M)
s=sub1(s,r'(?ms)\s*iget-object v0, p0, Lfjz;->j:Lpqq;.*?invoke-interface \{p0, v2\}, Lpqu;->b\(Ljava/util/Collection;\)Lpqu;\n','\n','fjz register metrics')
s=sub1(s,r'(?ms)\s*iget-object v0, p0, Lfjz;->k:Lpqw;.*?iput-object v1, p0, Lfjz;->k:Lpqw;\n\s*\.line 29\n\s*\.line 30\n\s*:cond_1','\n    const/4 v1, 0x0\n\n    :cond_1','fjz unregister metrics');p.write_text(s)
# fbl Agentic Dictation
p=R/'smali/fbl.smali';s=p.read_text();s=s.replace('.field private A:Lfda;\n','').replace('.field private final z:Lpqq;\n','');s=s.replace('.method public constructor <init>(Landroid/content/Context;Lpqu;Lpqq;)V','.method public constructor <init>(Landroid/content/Context;Lpqu;)V',1);s=sub1(s,r'(?m)^\s*iput-object p3, p0, Lfbl;->z:Lpqq;\n','', 'fbl ctor logger')
# p3 was formerly the metrics parameter and then reused as a Class temporary.
# With that parameter physically gone, use local v0 for the retained module
# lookup so the method contains no out-of-range p3 register.
s=sub1(s,r'const-class p3, Lgvs;','const-class v0, Lgvs;','fbl retained class temporary',flags=re.M)
s=sub1(s,r'invoke-virtual \{p2, p3\}, Lcom/google/android/libraries/inputmethod/module/ModuleManager;->b\(Ljava/lang/Class;\)Lptg;','invoke-virtual {p2, v0}, Lcom/google/android/libraries/inputmethod/module/ModuleManager;->b(Ljava/lang/Class;)Lptg;','fbl retained module lookup',flags=re.M)
s=sub1(s,r'(?ms)\s*new-instance v0, Lfda;.*?invoke-interface \{v1, v0\}, Lpqu;->b\(Ljava/util/Collection;\)Lpqu;\n','\n','fbl register metrics')
s=sub1(s,r'(?ms)^\s*:cond_5\n\s*iget-object v1, p0, Lfbl;->A:Lfda;.*?^\s*:cond_6\n','    :cond_5\n    :cond_6\n','fbl unregister metrics');p.write_text(s)
# ezc SignBoard
p=R/'smali/ezc.smali';s=p.read_text();s=s.replace('.field private final O:Lpqq;\n','').replace('.field private P:Lezi;\n','');s=s.replace('.method public constructor <init>(Landroid/content/Context;Lpqu;Lpqq;Lrlb;)V','.method public constructor <init>(Landroid/content/Context;Lpqu;Lrlb;)V',1);s=sub1(s,r'(?m)^\s*iput-object p3, p0, Lezc;->O:Lpqq;\n','', 'ezc ctor logger')
# Do not globally replace p4 with p3. p3 now carries the retained Lrlb and is
# later reused as the Leyw uninitialized reference; overwriting it with integer
# zero produced ART's "unable to initialize null ref" VerifyError. Rewrite the
# three affected instructions explicitly and use local v0 for the zero argument.
m=re.search(r'(?ms)^\.method public constructor <init>\(Landroid/content/Context;Lpqu;Lrlb;\)V\n.*?^\.end method',s,re.M)
if not m: raise SystemExit('ezc reduced constructor missing')
b=m.group(0)
b=sub1(b,r'iput-object p4, p0, Lezc;->I:Lrlb;','iput-object p3, p0, Lezc;->I:Lrlb;','ezc retained rlb parameter',flags=re.M)
b=sub1(b,r'const/4 p4, 0x0','const/4 v0, 0x0','ezc callable discriminator',flags=re.M)
b=sub1(b,r'invoke-direct \{p3, p0, p1, p4\}, Leyw;-><init>\(Ljava/lang/Object;Ljava/lang/Object;I\)V','invoke-direct {p3, p0, p1, v0}, Leyw;-><init>(Ljava/lang/Object;Ljava/lang/Object;I)V','ezc callable constructor',flags=re.M)
if re.search(r'\bp4\b',b): raise SystemExit('ezc reduced constructor still references p4')
s=s[:m.start()]+b+s[m.end():]
# The removed Lezi metrics-registration block happened to contain the Context
# load reused later by the retained Leye constructor. Reintroduce that load only;
# no metrics object or registration is restored.
s=sub1(s,r'(?ms)\s*new-instance v0, Lezi;.*?invoke-interface \{v1, v0\}, Lpqu;->b\(Ljava/util/Collection;\)Lpqu;\n','\n    iget-object v2, p0, Lezc;->g:Landroid/content/Context;\n','ezc register metrics')
s=sub1(s,r'(?ms)\s*iget-object v0, p0, Lezc;->P:Lezi;.*?iput-object v1, p0, Lezc;->P:Lezi;\n\s*\.line 39\n\s*\.line 40\n\s*:cond_2','\n    :cond_2','ezc unregister metrics');p.write_text(s)
# fwn Delight KLP downloader
p=R/'smali/fwn.smali';s=p.read_text();s=s.replace('.field private final c:Lpqq;\n','').replace('.field private e:Lfwp;\n','');s=s.replace('.method public constructor <init>(Landroid/content/Context;Lpqq;Lpqu;)V','.method public constructor <init>(Landroid/content/Context;Lpqu;)V',1);s=sub1(s,r'(?m)^\s*iput-object p2, p0, Lfwn;->c:Lpqq;\n','', 'fwn ctor logger')
# Preserve p2 as the retained Lwzf executor temporary. The removed p3 parameter
# was also used for two object temporaries; move those to local v3 rather than
# globally renaming p3 to p2, which created an uninitialized/self-typed call.
m=re.search(r'(?ms)^\.method public constructor <init>\(Landroid/content/Context;Lpqu;\)V\n.*?^\.end method',s,re.M)
if not m: raise SystemExit('fwn reduced constructor missing')
b=m.group(0)
b=sub1(b,r'iput-object p3, p0, Lfwn;->d:Lpqu;','iput-object p2, p0, Lfwn;->d:Lpqu;','fwn retained pqu parameter',flags=re.M)
b=sub1(b,r'new-instance p3, Lacmo;','new-instance v3, Lacmo;','fwn callback allocation',flags=re.M)
b=sub1(b,r'invoke-direct \{p3, p0\}, Lacmo;-><init>\(Ljava/lang/Object;\)V','invoke-direct {v3, p0}, Lacmo;-><init>(Ljava/lang/Object;)V','fwn callback init',flags=re.M)
b=sub1(b,r'iput-object p3, p0, Lfwn;->j:Lacmo;','iput-object v3, p0, Lfwn;->j:Lacmo;','fwn callback store',flags=re.M)
b=sub1(b,r'new-instance p3, Lfwm;','new-instance v3, Lfwm;','fwn manager allocation',flags=re.M)
b=sub1(b,r'invoke-direct \{p3, p1, v0, p2, v1\}, Lfwm;-><init>\(Landroid/content/Context;Lpli;Lwzf;Lnlt;\)V','invoke-direct {v3, p1, v0, p2, v1}, Lfwm;-><init>(Landroid/content/Context;Lpli;Lwzf;Lnlt;)V','fwn manager init',flags=re.M)
b=sub1(b,r'iput-object p3, p0, Lfwn;->b:Lfwm;','iput-object v3, p0, Lfwn;->b:Lfwm;','fwn manager store',flags=re.M)
if re.search(r'\bp3\b',b): raise SystemExit('fwn reduced constructor still references p3')
s=s[:m.start()]+b+s[m.end():]
s=sub1(s,r'(?ms)\s*new-instance p2, Lfwp;.*?invoke-interface \{p0, p2\}, Lpqu;->b\(Ljava/util/Collection;\)Lpqu;\n','\n','fwn register metrics')
s=sub1(s,r'(?ms)\s*iget-object v0, p0, Lfwn;->e:Lfwp;.*?iput-object v0, p0, Lfwn;->e:Lfwp;\n','\n','fwn unregister metrics');p.write_text(s)
# fxg Device Intelligence
p=R/'smali/fxg.smali';s=p.read_text();s=s.replace('.field private final k:Lpqq;\n','').replace('.field private l:Lfxk;\n','');s=s.replace('.method public constructor <init>(Lpqu;Lpqq;)V','.method public constructor <init>(Lpqu;)V',1);s=sub1(s,r'(?m)^\s*iput-object p2, p0, Lfxg;->k:Lpqq;\n','', 'fxg ctor logger')
s=sub1(s,r'(?ms)\s*new-instance v0, Lfxk;.*?invoke-interface \{p0, v0\}, Lpqu;->b\(Ljava/util/Collection;\)Lpqu;\n','\n','fxg register metrics')
s=sub1(s,r'(?ms)^\s*:cond_1\n\s*iget-object v0, p0, Lfxg;->l:Lfxk;.*?^\s*:cond_2\n','    :cond_1\n    :cond_2\n','fxg unregister metrics');p.write_text(s)
# jsj SuperInsert
p=R/'smali/jsj.smali';s=p.read_text();s=s.replace('.field private final u:Ljsx;\n','');s=s.replace('.method public constructor <init>(Landroid/content/Context;Lpqq;)V','.method public constructor <init>(Landroid/content/Context;)V',1);s=sub1(s,r'(?ms)\s*new-instance v0, Ljsx;.*?iput-object v0, p0, Ljsj;->u:Ljsx;\n','\n','jsj ctor metrics');m=re.search(r'(?ms)^\.method public constructor <init>\(Landroid/content/Context;\)V\n.*?^\.end method',s,re.M);b=m.group(0);b=b.replace('new-instance p2, Ljrw;','new-instance v0, Ljrw;').replace('invoke-direct {p2, p1}, Ljrw;-><init>(Landroid/content/Context;)V','invoke-direct {v0, p1}, Ljrw;-><init>(Landroid/content/Context;)V').replace('iput-object p2, p0, Ljsj;->r:Ljrw;','iput-object v0, p0, Ljsj;->r:Ljrw;');s=s[:m.start()]+b+s[m.end():]
s=sub1(s,r'(?ms)\s*invoke-static \{\}, Lpqr;->b\(\)Lpqu;.*?invoke-interface \{p1, p0\}, Lpqu;->a\(Lpqt;\)Lpqu;\n','\n','jsj register metrics')
s=sub1(s,r'(?ms)\s*invoke-static \{\}, Lpqr;->b\(\)Lpqu;.*?invoke-interface \{v0, p0\}, Lpqu;->c\(Ljava/lang/Class;\)Lpqu;\n','\n','jsj unregister metrics');p.write_text(s)
# Dagger/callsite constructor rewrites
p=R/'smali/eqt.smali';s=p.read_text();repls=[(r'invoke-direct \{v1, v0, p0\}, Lffw;-><init>\(Lpqu;Lpqq;\)V','invoke-direct {v1, v0}, Lffw;-><init>(Lpqu;)V'),(r'invoke-direct \{v1, v0, p0\}, Lfjz;-><init>\(Lpqu;Lpqq;\)V','invoke-direct {v1, v0}, Lfjz;-><init>(Lpqu;)V'),(r'invoke-direct \{v3, p0, v0, v1, v2\}, Lezc;-><init>\(Landroid/content/Context;Lpqu;Lpqq;Lrlb;\)V','invoke-direct {v3, p0, v0, v2}, Lezc;-><init>(Landroid/content/Context;Lpqu;Lrlb;)V'),(r'invoke-direct \{v2, v0, p0, v1\}, Lfwn;-><init>\(Landroid/content/Context;Lpqq;Lpqu;\)V','invoke-direct {v2, v0, v1}, Lfwn;-><init>(Landroid/content/Context;Lpqu;)V'),(r'invoke-direct \{v1, v0, p0\}, Lfxg;-><init>\(Lpqu;Lpqq;\)V','invoke-direct {v1, v0}, Lfxg;-><init>(Lpqu;)V'),(r'invoke-direct \{v1, p0, v0\}, Ljsj;-><init>\(Landroid/content/Context;Lpqq;\)V','invoke-direct {v1, p0}, Ljsj;-><init>(Landroid/content/Context;)V')]
for pat,r in repls:s=sub1(s,pat,r,'eqt '+r,flags=re.M)
p.write_text(s)
for rel,pat,r in [('smali/fbn.smali',r'invoke-direct \{v2, v0, v1, p0\}, Lfbl;-><init>\(Landroid/content/Context;Lpqu;Lpqq;\)V','invoke-direct {v2, v0, v1}, Lfbl;-><init>(Landroid/content/Context;Lpqu;)V'),('smali_classes2/fbp.smali',r'invoke-direct \{p0, p1, p2, p3\}, Lfbl;-><init>\(Landroid/content/Context;Lpqu;Lpqq;\)V','invoke-direct {p0, p1, p2}, Lfbl;-><init>(Landroid/content/Context;Lpqu;)V')]:
 p=R/rel;s=p.read_text();s=sub1(s,pat,r,rel,flags=re.M);p.write_text(s)
print('mixed feature metrics fields/ctor/lifecycle stripped; retained constructor register state repaired')
