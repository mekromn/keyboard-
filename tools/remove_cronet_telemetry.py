#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path('/mnt/data/meboard_work/buildtree')

def replace_exact(path, old, new, count=1):
    p=ROOT/path; s=p.read_text(); s2,n=s.replace(old,new,count),s.count(old)
    if n < count: raise SystemExit(f'{path}: expected {count} occurrence(s), found {n}')
    p.write_text(s2)

replace_exact(Path('smali/org/chromium/net/ExperimentalCronetEngine.smali'),
'''    invoke-static {p0}, Lacru;->b(Landroid/content/Context;)Z\n\n    .line 2\n    .line 3\n    .line 4\n    move-result v0\n''',
'''    const/4 v0, 0x0\n''')
replace_exact(Path('smali/acqm.smali'),
'''    invoke-static {p0}, Lacru;->b(Landroid/content/Context;)Z\n\n    .line 3\n    .line 4\n    .line 5\n    move-result v1\n''',
'''    const/4 v1, 0x0\n''')
replace_exact(Path('smali_classes3/org/chromium/net/impl/JavaCronetProvider.smali'),
'''    invoke-static {v0, v1}, Lacru;->c(Landroid/content/Context;Lacrp;)Z\n\n    .line 13\n    .line 14\n    .line 15\n    move-result v1\n''',
'''    const/4 v1, 0x0\n''')
replace_exact(Path('smali_classes3/acrt.smali'),
'''    invoke-static {p0, p1}, Lacru;->c(Landroid/content/Context;Lacrp;)Z\n\n    .line 15\n    .line 16\n    .line 17\n    move-result p0\n''',
'''    const/4 p0, 0x0\n''')

p=ROOT/'smali/acru.smali'; s=p.read_text()
for name,sig in [('b',r'b\(Landroid/content/Context;\)Z'),('c',r'c\(Landroid/content/Context;Lacrp;\)Z')]:
    pat=re.compile(rf'(?ms)^\.method public static {sig}\n.*?^\.end method\n?')
    s,n=pat.subn('',s,count=1)
    if n != 1: raise SystemExit(f'acru.{name}: expected method exactly once, got {n}')
p.write_text(s)

p=ROOT/'smali_classes3/bli$$ExternalSyntheticApiModelOutline0.smali'; s=p.read_text()
pat=re.compile(r'(?ms)^\.method public static bridge synthetic m\(Lcom/google/android/libraries/inputmethod/accounts/checker/AccountsCapabilitiesChangedReceiver;\)Ljava/lang/String;\n.*?^\.end method\n?')
s,n=pat.subn('',s,count=1)
if n != 1: raise SystemExit(f'account receiver synthetic bridge: expected once, got {n}')
p.write_text(s)

for p in ROOT.glob('smali*/**/*.smali'):
    t=p.read_text(errors='ignore')
    if 'android.net.http.EnableTelemetry' in t:
        raise SystemExit(f'telemetry key remains in {p}')
    if 'AccountsCapabilitiesChangedReceiver' in t:
        raise SystemExit(f'account receiver reference remains in {p}')
print('Removed Cronet telemetry metadata/config capability and stale account receiver bridge')
