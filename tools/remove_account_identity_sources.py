#!/usr/bin/env python3
from pathlib import Path
import re
R=Path('/mnt/data/meboard_work/buildtree')
def sub1(s,p,r,d,flags=re.M|re.S):
 o,n=re.subn(p,r,s,count=1,flags=flags)
 if n!=1: raise SystemExit(f'{d}: {n}')
 return o
# Email LM: preserve local learned emails, remove device-account seed loop.
p=R/'smali/fuu.smali';s=p.read_text();s=sub1(s,r'(?ms)    iget-object v4, p0, Lfuu;->a:Landroid/content/Context;\n.*?    :cond_2\n    const/4 v4, 0x0\n','    const/4 v6, 0x1\n\n    const/4 v4, 0x0\n','fuu account seed');p.write_text(s)
# Remove the account-only refresh runnable scheduling.
p=R/'smali/fuv.smali';s=p.read_text();s=sub1(s,r'(?ms)(    invoke-virtual \{v0, v2\}, Ljava/util/concurrent/atomic/AtomicBoolean;->set\(Z\)V\n).*?(    :cond_1\n    :goto_0\n    return-void)',r'\1\n    goto :goto_0\n\n\2','fuv account refresh');p.write_text(s)
# cyv discriminator 2 is that removed refresh path.
p=R/'smali/cyv.smali';s=p.read_text();s=sub1(s,r'(?ms)^\.method public constructor <init>\(Lfuv;Lfuu;Landroid/content/Context;I\)V\n.*?^\.end method\n?','','cyv account ctor');s=sub1(s,r'(?ms)    const/4 v3, 0x2\n\n    \.line 10\n    if-eq v0, v3, :cond_2\n\n    \.line 11\n    \.line 12\n','','cyv dispatch');s=sub1(s,r'(?ms)^    :cond_2\n.*?(?=^    :cond_4\n)','','cyv account branch');p.write_text(s)
# Delete raw AccountManager enumeration helper.
p=R/'smali/dov.smali';s=p.read_text();s=sub1(s,r'(?ms)^\.method public static n\(Landroid/content/Context;\)Ljava/util/List;\n.*?^\.end method\n?','','dov n');p.write_text(s)
# Help/feedback keeps functionality but always uses its existing anonymous identity.
p=R/'smali/rzb.smali';s=p.read_text();s=sub1(s,r'(?ms)^\.method public static i\(Landroid/content/Context;ZZ\)Llfd;\n.*?^\.end method','''.method public static i(Landroid/content/Context;ZZ)Llfd;\n    .locals 1\n    new-instance v0, Llfd;\n    invoke-direct {v0, p0}, Llfd;-><init>(Landroid/content/Context;)V\n    iput-boolean p1, v0, Llfd;->c:Z\n    const-string p0, "anonymous"\n    iput-object p0, v0, Llfd;->a:Ljava/lang/String;\n    return-object v0\n.end method''','anonymous feedback');p.write_text(s)
# MDD/download dependency had a discarded AccountManager acquisition; remove only that call.
p=R/'smali/unb.smali';s=p.read_text();s,n=re.subn(r'(?m)^\s*invoke-static \{p1\}, Landroid/accounts/AccountManager;->get\(Landroid/content/Context;\)Landroid/accounts/AccountManager;\n','',s,count=1);assert n==1;p.write_text(s)
# Mozc: remove self-account provider, keep contacts and user dictionaries.
p=R/'smali/iah.smali';s=p.read_text();s=s.replace('.field public final e:Lvpu;\n\n','',1);s=sub1(s,r'(?ms)    new-instance v1, Lexg;\n\n    \.line 34\n.*?    iput-object v1, p0, Liah;->e:Lvpu;\n\n    \.line 41\n    \.line 42\n','','iah account provider');p.write_text(s)
# exg case 19 built AccountManager + Mozc importer.
p=R/'smali/exg.smali';s=p.read_text();m=re.search(r'(?ms)(:pswitch_data_0\n\s*\.packed-switch 0x0\n)(.*?)(\s*\.end packed-switch)',s);ls=m.group(2).splitlines();idx=[i for i,l in enumerate(ls) if ':pswitch_' in l];assert ':pswitch_0' in ls[idx[19]];ls[idx[19]]=ls[idx[19]].replace(':pswitch_0',':pswitch_1');s=s[:m.start(2)]+'\n'.join(ls)+s[m.end(2):];s=sub1(s,r'(?ms)^    :pswitch_0\n.*?(?=^    :pswitch_1\n)','','exg account case');p.write_text(s)
# hyc case3 imported all account names; case4 also cleared that private account dictionary.
p=R/'smali_classes2/hyc.smali';s=p.read_text();m=re.search(r'(?ms)(:pswitch_data_0\n\s*\.packed-switch 0x0\n)(.*?)(\s*\.end packed-switch)',s);ls=m.group(2).splitlines();idx=[i for i,l in enumerate(ls) if ':pswitch_' in l];assert ':pswitch_10' in ls[idx[3]];ls[idx[3]]=ls[idx[3]].replace(':pswitch_10',':pswitch_11');s=s[:m.start(2)]+'\n'.join(ls)+s[m.end(2):];s=sub1(s,r'(?ms)^    :pswitch_10\n.*?(?=^    :pswitch_11\n)','','hyc account import');a=s.index('    iget-object p0, p0, Liah;->e:Lvpu;');b=s.index('    :catchall_1\n',a);assert '__auto_imported_self_accounts' in s[a:b];s=s[:a]+'    return-void\n\n'+s[b:];p.write_text(s)
for n in ['__auto_imported_self_accounts','Ldov;->n(Landroid/content/Context;)Ljava/util/List;','Liah;->e:Lvpu;','getAccounts()[Landroid/accounts/Account;']:
 h=[x for x in R.glob('smali*/**/*.smali') if n in x.read_text(errors='ignore')]
 if h: raise SystemExit((n,h[:10]))
print('Removed account-derived Email LM/Mozc inputs and forced anonymous feedback; features retained')
