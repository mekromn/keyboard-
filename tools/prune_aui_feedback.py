from pathlib import Path
import re
p=Path('/mnt/data/meboard_work/buildtree/smali_classes2/aui.smali')
s=p.read_text()
# Case 4 is the retired AgenticDictationFeedbackAccessPointProvider callback.
# Repoint the impossible packed-switch entry to the adjacent harmless retained case,
# then physically delete :pswitch_d and its private :cond_3 body.
dm=re.search(r'(?ms)(:pswitch_data_0\s*\n\s*\.packed-switch 0x0\s*\n)(.*?)(\s*\.end packed-switch)',s)
if not dm: raise SystemExit('switch table not found')
labels=re.findall(r':pswitch_[0-9a-f]+',dm.group(2))
if len(labels)<5 or labels[4] != ':pswitch_d': raise SystemExit(f'unexpected case4 mapping: {labels[:6]}')
lines=dm.group(2).splitlines()
seen=0
for i,line in enumerate(lines):
    if re.search(r':pswitch_[0-9a-f]+',line):
        if seen==4:
            lines[i]=line.replace(':pswitch_d',':pswitch_e')
            break
        seen+=1
newtable='\n'.join(lines)
s=s[:dm.start(2)]+newtable+s[dm.end(2):]
# Delete retired branch body from its code label through the next case label.
m=re.search(r'(?ms)^\s*:pswitch_d\s*$.*?(?=^\s*:pswitch_e\s*$)',s)
if not m: raise SystemExit('feedback branch body not found')
s=s[:m.start()]+s[m.end():]
p.write_text(s)
print('pruned Laui case 4 feedback callback')
