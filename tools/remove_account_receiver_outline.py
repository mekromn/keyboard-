#!/usr/bin/env python3
"""Remove the R8 API-model bridge dedicated to account-capability broadcasts."""
from pathlib import Path
import re

ROOT = Path('/mnt/data/meboard_work/buildtree')
P = ROOT / 'smali_classes3/bli$$ExternalSyntheticApiModelOutline0.smali'
text = P.read_text()
pattern = re.compile(
    r'(?ms)^\.method public static bridge synthetic m\('
    r'Lcom/google/android/libraries/inputmethod/accounts/checker/'
    r'AccountsCapabilitiesChangedReceiver;\)Ljava/lang/String;\n'
    r'.*?^\.end method\n?'
)
text, count = pattern.subn('', text, count=1)
if count != 1:
    raise SystemExit(f'expected one account-capability API-model bridge, removed {count}')
P.write_text(text)
print('physically removed synthetic account-capability receiver bridge')
