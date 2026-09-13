#!/usr/bin/env python3
from pathlib import Path
import argparse
p=argparse.ArgumentParser(); p.add_argument('smali',type=Path); a=p.parse_args()
s=a.smali.read_text()
method='.method public final onStartInput(Landroid/view/inputmethod/EditorInfo;Z)V'
st=s.index(method); en=s.index('\n.end method',st); m=s[st:en]
entry=m.index('move-object/from16 v0, p0')
entry_pin=m.index('move-object v14, v0',entry)
early=m.index('goto/16 :goto_4',entry)
late_pin=m.rindex('move-object v14, v0')
join=m.index(':goto_4',late_pin)
read=m.index('iget-object v1, v14, Loup;->j:',join)
assert entry < entry_pin < early < late_pin < join < read
assert m.count('move-object v14, v0') >= 2
print('PASS: v14=Loup is defined on both early and normal predecessors of :goto_4 before glass-hook read')
