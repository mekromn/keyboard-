#!/usr/bin/env python3
"""Repair the remaining Stage-31/31a verifier defect in oup.onStartInput.

Stage 31a saved the Loup receiver into v14 only near the normal method tail.
An existing early stock `goto :goto_4` reaches the added Meboard glass hook
without traversing that assignment. Initialize v14 with p0 at method entry so
every predecessor of :goto_4 carries a valid Loup receiver. The normal late
assignment is deliberately retained as a second type pin after stock reuses v14.
"""
from pathlib import Path
import argparse

p=argparse.ArgumentParser()
p.add_argument('decoded_root',type=Path)
a=p.parse_args()
f=a.decoded_root/'smali'/'oup.smali'
s=f.read_text()
method='.method public final onStartInput(Landroid/view/inputmethod/EditorInfo;Z)V'
start=s.index(method)
end=s.index('\n.end method',start)
m=s[start:end]
needle='''    .line 1\n    move-object/from16 v0, p0\n'''
replacement=needle+'\n    move-object v14, v0\n'
if replacement in m:
    raise SystemExit('Stage-31b entry repair already present')
if needle not in m:
    raise SystemExit('Unexpected onStartInput entry; refusing to patch')
m=m.replace(needle,replacement,1)
f.write_text(s[:start]+m+s[end:])
print('Stage-31b: initialized v14=Loup at onStartInput entry')
