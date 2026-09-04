#!/usr/bin/env python3
"""Remove the detached feature-flagged Clearcut forwarding wrapper."""
from pathlib import Path
import re

ROOT = Path('/mnt/data/meboard_work/buildtree')
GQN = ROOT / 'smali/gqn.smali'
FOL = ROOT / 'smali/fol.smali'
if not GQN.exists() or not FOL.exists():
    raise SystemExit('gqn/fol missing')

gqn = GQN.read_text()
fol = FOL.read_text()
if (
    '.implements Lpqq;' not in gqn
    or 'new-instance p1, Lfol;' not in gqn
    or 'const/4 v0, 0x2' not in gqn
):
    raise SystemExit('unexpected gqn layout')

refs = []
for path in ROOT.glob('smali*/**/*.smali'):
    if path != GQN and 'Lgqn;' in path.read_text(errors='ignore'):
        refs.append(str(path.relative_to(ROOT)))
if refs != ['smali/fol.smali']:
    raise SystemExit(f'unexpected gqn inbound refs: {refs}')

# gqn registers fol discriminator 2. In fol's packed switch, that maps to
# :pswitch_e, whose only behavior updates gqn's AtomicBoolean gate.
data_match = re.search(
    r'(?ms)(:pswitch_data_0\s*\n\s*\.packed-switch\s+0x0\s*\n)'
    r'(.*?)'
    r'(\s*\.end packed-switch)',
    fol,
)
if not data_match:
    raise SystemExit('fol switch data missing')
labels = re.findall(r':pswitch_[0-9a-f]+', data_match.group(2))
if len(labels) < 3 or labels[2] != ':pswitch_e':
    raise SystemExit(f'fol case2 unexpected: {labels[:4]}')

data = data_match.group(2)
data, count = re.subn(
    r'(?m)^(\s*):pswitch_e\s*$',
    r'\1:pswitch_f',
    data,
    count=1,
)
if count != 1:
    raise SystemExit('fol case2 table rewrite failed')
fol = fol[:data_match.start(2)] + data + fol[data_match.end(2):]

data_pos = fol.rfind(':pswitch_data_0')
labels_in_code = list(re.finditer(r'(?m)^\s*:pswitch_e\s*$', fol[:data_pos]))
if len(labels_in_code) != 1:
    raise SystemExit(f'fol case2 code labels {len(labels_in_code)}')
start = labels_in_code[0].start()
next_case = re.search(
    r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',
    fol[labels_in_code[0].end():data_pos],
)
end = (
    labels_in_code[0].end() + next_case.start()
    if next_case
    else data_pos
)
segment = fol[start:end]
if 'Lgqn;' not in segment or 'AtomicBoolean;->set' not in segment:
    raise SystemExit('fol case2 is not the gqn flag callback')

FOL.write_text(fol[:start] + fol[end:])
GQN.unlink()
for path in ROOT.glob('smali*/**/*.smali'):
    if 'Lgqn;' in path.read_text(errors='ignore'):
        raise SystemExit(f'residual gqn reference: {path}')

print('physically removed gqn Clearcut forwarding wrapper and fol case 2 callback')
