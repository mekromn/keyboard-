#!/usr/bin/env python3
from pathlib import Path
import argparse

p = argparse.ArgumentParser(description='Repair the Stage-31 oup.onStartInput register-type verifier bug.')
p.add_argument('decoded_root', type=Path)
a = p.parse_args()

f = a.decoded_root / 'smali' / 'oup.smali'
s = f.read_text()

old = '''    .line 380\n    .line 381\n    .line 382\n    iget-object v0, v0, Loup;->ag:Louq;\n'''
new = '''    .line 380\n    .line 381\n    .line 382\n    move-object v14, v0\n\n    iget-object v0, v0, Loup;->ag:Louq;\n'''
assert old in s, 'Stage-31 pre-overwrite sequence not found or input drifted'
s = s.replace(old, new, 1)

old = '''    :cond_9\n    :goto_4\n    iget-object v1, v0, Loup;->j:Lcom/google/android/libraries/inputmethod/inputview/InputView;\n'''
new = '''    :cond_9\n    :goto_4\n    iget-object v1, v14, Loup;->j:Lcom/google/android/libraries/inputmethod/inputview/InputView;\n'''
assert old in s, 'Stage-31 invalid receiver sequence not found or input drifted'
f.write_text(s.replace(old, new, 1))
