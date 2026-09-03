#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path('/mnt/data/meboard_work/buildtree')

def sub1(s,pat,repl,desc,flags=re.M|re.S):
    o,n=re.subn(pat,repl,s,count=1,flags=flags)
    if n!=1: raise SystemExit(f'{desc}: expected 1 got {n}')
    return o

def rm_method(s,sig_re,desc):
    return sub1(s,rf'(?ms)^\.method[^\n]*{sig_re}\n.*?^\.end method\n?','',desc)

for rel,pat,repl,desc in [
 ('smali/evm.smali',r'invoke-static \{v1\}, Lmpo;->a\(Landroid/content/Context;\)Z\n(?:\s*\.line \d+\n)*\s*move-result v1','const/4 v1, 0x0','evm Google account fallback'),
 ('smali/nlq.smali',r'invoke-static \{v2\}, Lmpo;->a\(Landroid/content/Context;\)Z\n(?:\s*\.line \d+\n)*\s*move-result v2','const/4 v2, 0x0','nlq Google account fallback'),
]:
 p=ROOT/rel;s=p.read_text();s=sub1(s,pat,repl,desc);p.write_text(s)
for cls in ['mpo','ksg']:
 hits=list(ROOT.glob(f'smali*/**/{cls}.smali'))
 if len(hits)!=1: raise SystemExit((cls,hits))
 hits[0].unlink(); print('deleted',cls)
manifest=ROOT/'AndroidManifest.xml'; s=manifest.read_text()
s,n=re.subn(r'(?m)^\s*<uses-permission[^>]*android:name="android\.permission\.GET_ACCOUNTS"[^>]*/>\s*\n?','',s,count=1)
if n!=1: raise SystemExit(f'GET_ACCOUNTS manifest count {n}')
s,n=re.subn(r'(?ms)\s*<receiver[^>]*android:name="com\.google\.android\.libraries\.inputmethod\.accounts\.checker\.AccountsCapabilitiesChangedReceiver".*?</receiver>','',s,count=1)
if n!=1: s,n=re.subn(r'(?ms)\s*<receiver[^>]*android:name="com\.google\.android\.libraries\.inputmethod\.accounts\.checker\.AccountsCapabilitiesChangedReceiver"[^>]*/>','',s,count=1)
if n!=1: raise SystemExit(f'account receiver manifest count {n}')
manifest.write_text(s)
p=ROOT/'smali/eqt.smali'; lines=p.read_text().splitlines()
mi=next(i for i,l in enumerate(lines) if l.startswith('.method public final aI()Ljava/util/Set;'))
me=next(i for i in range(mi+1,len(lines)) if lines[i]=='.end method')
m=lines[mi:me+1];arr=next(i for i,l in enumerate(m) if re.search(r'new-array\s+v11,\s+v11,\s+\[Lpth;',l))
start=end=None
for i in range(arr+1,len(m)):
 if 'new-instance v4, Lkbk;' in m[i]:
  blk='\n'.join(m[i:i+10])
  if 'const/4 v12, 0x3' in blk and 'Lkbk;-><init>(I)V' in blk:
   start=i; end=next(j for j in range(i,len(m)) if re.match(r'\s*aput-object\s+v4,\s+v11,\s+v23',m[j])); break
if start is None: raise SystemExit('eqt kbk3 registry block not found')
del m[start:end+1]
out=[];idx=0
for line in m:
 if re.match(r'\s*aput-object\s+\w+,\s+v11,\s+v23\s*$',line):
  while out and re.match(r'\s*const/16\s+v23,\s+0x[0-9a-f]+\s*$',out[-1]): out.pop()
  out.append(f'    const/16 v23, 0x{idx:x}'); out.append(line); idx+=1
 else: out.append(line)
m=out;arr=next(i for i,l in enumerate(m) if 'new-array v11, v11, [Lpth;' in l)
for j in range(arr-1,max(-1,arr-12),-1):
 if re.match(r'\s*const/16\s+v11,\s+0x[0-9a-f]+\s*$',m[j]): m[j]=f'    const/16 v11, 0x{idx:x}';break
else: raise SystemExit('registry length const not found')
lines[mi:me+1]=m;text='\n'.join(lines)+'\n'
text,n=re.subn(r'(?m)^\.implements Lmpi;\n','',text,count=1)
if n!=1: raise SystemExit('eqt implements mpi')
text=rm_method(text,r'S\(\)Lmph;','eqt S mph provider');p.write_text(text)
p=ROOT/'smali/kbk.smali'; s=p.read_text();methods=[];pos=0
while True:
 mm=re.search(r'^\.method[^\n]*\n',s[pos:],re.M)
 if not mm: break
 a=pos+mm.start(); b=s.find('\n.end method',pos+mm.end())
 if b<0: break
 b+=len('\n.end method'); methods.append((a,b,s[a:b]));pos=b
changed=0
for a,b,body in reversed(methods):
 if 'packed-switch' not in body: continue
 dm=re.search(r'(?ms)(:pswitch_data_0\s*\n\s*\.packed-switch 0x0\s*\n)(.*?)(\s*\.end packed-switch)',body)
 if not dm: continue
 labels=re.findall(r':pswitch_[0-9a-f]+',dm.group(2))
 if len(labels)<4: continue
 lab=labels[3]
 if lab!=':pswitch_4': raise SystemExit(f'kbk case3 unexpected {lab}')
 data=dm.group(2); data,n=re.subn(r'(?m)^(\s*):pswitch_4\s*$',r'\1:pswitch_5',data,count=1)
 if n!=1: raise SystemExit('kbk table rewrite')
 body=body[:dm.start(2)]+data+body[dm.end(2):];data_pos=body.rfind(':pswitch_data_0');ms=list(re.finditer(r'(?m)^\s*:pswitch_4\s*$',body[:data_pos]))
 if not ms: raise SystemExit('kbk code case3 label')
 st=ms[-1].start(); nxt=re.search(r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',body[ms[-1].end():data_pos]); en=ms[-1].end()+nxt.start() if nxt else data_pos
 body=body[:st]+body[en:];s=s[:a]+body+s[b:];changed+=1
if changed!=2: raise SystemExit(f'kbk case3 methods {changed}')
p.write_text(s); (ROOT/'smali/mpi.smali').unlink()
p=ROOT/'smali/cfu.smali'; s=p.read_text();s=rm_method(s,r'constructor <init>\(Lmph;Lablu;I\)V','cfu mph ctor');s=rm_method(s,r'constructor <init>\(Lmph;Lablu;I\[B\)V','cfu mph ctor byte')
s=sub1(s,r'(?ms)(\.method public final synthetic a\(Ljava/lang/Object;Ljava/lang/Object;\)Ljava/lang/Object;.*?if-eq v0, v1, :cond_1\n).*?(    :cond_1\n)',r'\1\n    goto :cond_1\n\n\2','cfu a account cases')
s=sub1(s,r'(?ms)(\.method public final b\(Ljava/lang/Object;\)Ljava/lang/Object;.*?if-eq v0, v3, :cond_7\n).*?(    :cond_7\n)',r'\1\n    goto :cond_7\n\n\2','cfu b account cases')
s=sub1(s,r'(?ms)(\.method public final c\(Ljava/lang/Object;Lablu;\)Lablu;.*?if-eq v0, v2, :cond_1\n).*?(    :cond_1\n)',r'\1\n    goto :cond_1\n\n\2','cfu c account cases');p.write_text(s)
p=ROOT/'smali/bqu.smali'; s=p.read_text(); s=rm_method(s,r'constructor <init>\(Lmph;Lablu;I\)V','bqu mph ctor');methods=[];pos=0
while True:
 mm=re.search(r'^\.method[^\n]*\n',s[pos:],re.M)
 if not mm: break
 a=pos+mm.start();b=s.find('\n.end method',pos+mm.end())
 if b<0:break
 b+=len('\n.end method');methods.append((a,b,s[a:b]));pos=b
changed=0
for a,b,body in reversed(methods):
 dm=re.search(r'(?ms)(:pswitch_data_0\s*\n\s*\.packed-switch 0x0\s*\n)(.*?)(\s*\.end packed-switch)',body)
 if not dm: continue
 labels=re.findall(r':pswitch_[0-9a-f]+',dm.group(2))
 if len(labels)<=9: continue
 lab=labels[9]; repl=labels[8];data=dm.group(2); data,n=re.subn(rf'(?m)^(\s*){re.escape(lab)}\s*$',rf'\1{repl}',data,count=1)
 if n!=1: raise SystemExit('bqu table')
 body=body[:dm.start(2)]+data+body[dm.end(2):];data_pos=body.rfind(':pswitch_data_0');ms=list(re.finditer(rf'(?m)^\s*{re.escape(lab)}\s*$',body[:data_pos]))
 if not ms: raise SystemExit(('bqu label',lab))
 st=ms[-1].start();nxt=re.search(r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',body[ms[-1].end():data_pos]);en=ms[-1].end()+nxt.start() if nxt else data_pos;seg=body[st:en];outside=body[:st]+body[en:data_pos];pres=en
 for lm in re.finditer(r'(?m)^\s*(:[A-Za-z0-9_]+)\s*$',seg):
  l=lm.group(1)
  if l.startswith(':pswitch_'): continue
  if re.search(rf'(?<![A-Za-z0-9_]){re.escape(l)}(?![A-Za-z0-9_])',outside): pres=min(pres,st+lm.start())
 body=body[:st]+body[pres:];s=s[:a]+body+s[b:];changed+=1
if changed!=3: raise SystemExit(f'bqu case9 changed {changed}')
p.write_text(s)
p=ROOT/'smali/mpg.smali'; s=p.read_text();s,n=re.subn(r'(?m)^\s*if-eqz v0, :cond_3\n','',s,count=1); assert n==1;s=sub1(s,r'(?ms)^    :cond_3\n.*?(?=^\.end method)','', 'mpg account branch'); p.write_text(s)
p=ROOT/'smali_classes2/mpf.smali'; s=p.read_text(); s=rm_method(s,r'constructor <init>\(Ljava/lang/String;Lmph;Lablu;I\)V','mpf mph ctor')
for label,methodsig,desc in [(':cond_2',r'a\(Ljava/lang/Object;Ljava/lang/Object;\)Ljava/lang/Object;','mpf a'),(':cond_d',r'b\(Ljava/lang/Object;\)Ljava/lang/Object;','mpf b'),(':cond_2',r'c\(Ljava/lang/Object;Lablu;\)Lablu;','mpf c')]:
 mm=re.search(rf'(?ms)^\.method[^\n]*{methodsig}\n.*?^\.end method',s,re.M)
 if not mm: raise SystemExit(desc+' method')
 body=mm.group(0);body,n=re.subn(rf'(?m)^\s*if-eqz v0, {re.escape(label)}\n','',body,count=1)
 if n!=1: raise SystemExit(desc+' zero jump')
 pos=body.find('\n    '+label+'\n')
 if pos<0: raise SystemExit(desc+' label')
 body=body[:pos]+'\n.end method';s=s[:mm.start()]+body+s[mm.end():]
p.write_text(s)
receiver=ROOT/'smali_classes2/com/google/android/libraries/inputmethod/accounts/checker/AccountsCapabilitiesChangedReceiver.smali'
if receiver.exists(): receiver.unlink()
for c in ['mph','moz','mpb','mpc','mpd','mpe']:
 hits=list(ROOT.glob(f'smali*/**/{c}.smali'))
 if len(hits)!=1: raise SystemExit((c,hits))
 hits[0].unlink()
for needle in ['Landroid/accounts/AccountManager;->get','getAccounts()[Landroid/accounts/Account;','const-string p0, "get_accounts"','Lmph;','AccountsCapabilitiesChangedReceiver','android.permission.GET_ACCOUNTS','Lmpo;']:
 hits=[]
 for f in list(ROOT.glob('smali*/**/*.smali'))+[ROOT/'AndroidManifest.xml']:
  if f.exists() and needle in f.read_text(errors='ignore'): hits.append(str(f.relative_to(ROOT)))
 if hits: raise SystemExit(f'residual {needle}: {hits[:30]}')
print('account status/discovery implementation removed')
