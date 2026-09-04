#!/usr/bin/env python3
"""Remove Latin5 metrics export while preserving Latin5/Delight5 local AI.

This deletes only the Latin5ProcessorProvider, counter/native-metrics processors,
and their Clearcut bridge. The Delight5 facilitator, decoder, language models,
local personalization, and on-device voice implementation remain untouched.
"""
from pathlib import Path
import re

ROOT = Path('/mnt/data/meboard_work/buildtree')
EQT = ROOT / 'smali/eqt.smali'


def find(cls: str) -> Path:
    hits = list(ROOT.glob(f'smali*/**/{cls}.smali'))
    if len(hits) != 1:
        raise SystemExit(f'{cls}: expected exactly one class file, got {hits}')
    return hits[0]


def method_ranges(text: str):
    out = []
    pos = 0
    while True:
        m = re.search(r'^\.method[^\n]*\n', text[pos:], re.M)
        if not m:
            break
        start = pos + m.start()
        end = text.find('\n.end method', pos + m.end())
        if end < 0:
            raise SystemExit('unterminated smali method')
        end += len('\n.end method')
        out.append((start, end, text[start:end]))
        pos = end
    return out


def remove_registry_factory(text: str, dispatcher: str, discriminator: int) -> str:
    mm = re.search(r'(?ms)^\.method public final aI\(\)Ljava/util/Set;\n.*?^\.end method', text, re.M)
    if not mm:
        raise SystemExit('eqt.aI module registry missing')
    lines = mm.group(0).splitlines()
    arr = next((i for i, line in enumerate(lines) if 'new-array v11, v11, [Lpth;' in line), None)
    if arr is None:
        raise SystemExit('eqt.aI module array missing')

    regs = {}
    target = None
    pending = None
    for i, line in enumerate(lines):
        s = line.strip()
        c = re.match(r'const(?:/4|/16)?\s+(v\d+),\s+(-?0x[0-9a-f]+|-?\d+)', s)
        if c:
            regs[c.group(1)] = int(c.group(2), 0)
        mv = re.match(r'move(?:/from16|/16)?\s+(v\d+),\s+(v\d+)', s)
        if mv:
            regs[mv.group(1)] = regs.get(mv.group(2))
        ctor = re.match(r'invoke-direct \{(v\d+),\s*(v\d+)\}, L([^;]+);-><init>\(I\)V', s)
        if ctor and ctor.group(3) == dispatcher and regs.get(ctor.group(2)) == discriminator:
            obj = ctor.group(1)
            start = next((j for j in range(i, arr, -1)
                          if re.match(rf'\s*new-instance\s+{re.escape(obj)},\s+L{re.escape(dispatcher)};', lines[j])), None)
            if start is None:
                raise SystemExit(f'{dispatcher}/{discriminator}: allocation missing')
            pending = (start, obj)
        if pending and re.match(rf'\s*aput-object\s+{re.escape(pending[1])},\s+v11,\s+v23\s*$', line):
            if target is not None:
                raise SystemExit(f'{dispatcher}/{discriminator}: duplicate registry factory')
            target = (pending[0], i)
            pending = None
    if target is None:
        raise SystemExit(f'{dispatcher}/{discriminator}: registry factory missing')

    del lines[target[0]:target[1] + 1]
    arr = next(i for i, line in enumerate(lines) if 'new-array v11, v11, [Lpth;' in line)
    stores = [i for i in range(arr + 1, len(lines))
              if re.match(r'\s*aput-object\s+\w+,\s+v11,\s+v23\s*$', lines[i])]
    offset = 0
    for idx, pos0 in enumerate(stores):
        pos = pos0 + offset
        while pos > 0 and re.match(r'\s*const/16\s+v23,\s+0x[0-9a-f]+\s*$', lines[pos - 1]):
            del lines[pos - 1]
            pos -= 1
            offset -= 1
        lines.insert(pos, f'    const/16 v23, 0x{idx:x}')
        offset += 1
    arr = next(i for i, line in enumerate(lines) if 'new-array v11, v11, [Lpth;' in line)
    for j in range(arr - 1, max(-1, arr - 16), -1):
        if re.match(r'\s*const/16\s+v11,\s+0x[0-9a-f]+\s*$', lines[j]):
            lines[j] = f'    const/16 v11, 0x{len(stores):x}'
            break
    else:
        raise SystemExit('eqt.aI module-count constant missing')
    print(f'eqt.aI: removed {dispatcher} discriminator {discriminator}; registry now {len(stores)}')
    return text[:mm.start()] + '\n'.join(lines) + text[mm.end():]


def prune_case(cls: str, case: int, target_type: str, expected: int) -> None:
    p = find(cls)
    text = p.read_text()
    changed = 0
    for a, b, body in reversed(method_ranges(text)):
        if f'L{target_type};' not in body or 'packed-switch' not in body:
            continue
        for dm in list(re.finditer(
            r'(?ms)(^\s*:pswitch_data_[0-9a-f]+\s*\n\s*\.packed-switch\s+0x([0-9a-f]+)\s*\n)(.*?)(^\s*\.end packed-switch)',
            body, re.M))[::-1]:
            base = int(dm.group(2), 16)
            labels = re.findall(r':pswitch_[0-9a-f]+', dm.group(3))
            cmap = {base + i: label for i, label in enumerate(labels)}
            if case not in cmap:
                continue
            label = cmap[case]
            data_pos = dm.start()
            code_labels = list(re.finditer(rf'(?m)^\s*{re.escape(label)}\s*$', body[:data_pos]))
            if not code_labels:
                continue
            start = code_labels[-1].start()
            nxt = re.search(r'(?m)^\s*:pswitch_[0-9a-f]+\s*$', body[code_labels[-1].end():data_pos])
            end = code_labels[-1].end() + nxt.start() if nxt else data_pos
            if f'L{target_type};' not in body[start:end]:
                continue
            retained = [x for x in cmap if x != case]
            replacement = cmap[min(retained, key=lambda x: abs(x - case))]
            table, n = re.subn(rf'(?m)^(\s*){re.escape(label)}\s*$', rf'\1{replacement}', dm.group(3), count=1)
            if n != 1:
                raise SystemExit(f'{cls}: failed to rewrite case {case}')
            body = body[:dm.start(3)] + table + body[dm.end(3):]
            data_pos = body.rfind(dm.group(1).splitlines()[0].strip())
            code_labels = list(re.finditer(rf'(?m)^\s*{re.escape(label)}\s*$', body[:data_pos]))
            start = code_labels[-1].start()
            nxt = re.search(r'(?m)^\s*:pswitch_[0-9a-f]+\s*$', body[code_labels[-1].end():data_pos])
            end = code_labels[-1].end() + nxt.start() if nxt else data_pos
            segment = body[start:end]
            outside = body[:start] + body[end:data_pos]
            preserve = end
            for lm in re.finditer(r'(?m)^\s*(:[A-Za-z0-9_]+)\s*$', segment):
                internal = lm.group(1)
                if internal.startswith(':pswitch_'):
                    continue
                if re.search(rf'(?<![A-Za-z0-9_]){re.escape(internal)}(?![A-Za-z0-9_])', outside):
                    preserve = min(preserve, start + lm.start())
            body = body[:start] + body[preserve:]
            changed += 1
        text = text[:a] + body + text[b:]
    if changed != expected:
        raise SystemExit(f'{cls}: expected {expected} case-{case} branch removals, got {changed}')
    if f'L{target_type};' in text:
        raise SystemExit(f'{cls}: {target_type} reference remains after pruning')
    p.write_text(text)
    print(f'{cls}: removed case {case} telemetry branch x{changed}')


# Remove the module root and its Dagger provider/interface.
text = remove_registry_factory(EQT.read_text(), 'hal', 18)
text, n = re.subn(r'(?m)^\.implements Lhwq;\n', '', text, count=1)
if n != 1:
    raise SystemExit('eqt implements hwq missing')
text, n = re.subn(r'(?ms)^\.method public final x\(\)Lhwp;\n.*?^\.end method\n?', '', text, count=1)
if n != 1:
    raise SystemExit('eqt x()Lhwp provider missing')
EQT.write_text(text)
print('eqt: removed Latin5 metrics provider x() and hwq interface')

# Delete the module create/definition branches and the shared native-metric callback.
prune_case('hal', 18, 'hwp', 2)
prune_case('gzn', 17, 'hwn', 1)

DELETE = {'hwl', 'hwm', 'hwn', 'hwo', 'hwp', 'hwq', 'hwr'}
classes = {}
for p in ROOT.glob('smali*/**/*.smali'):
    t = p.read_text(errors='ignore')
    m = re.search(r'^\.class[^\n]* L([^;]+);', t, re.M)
    if m:
        classes[m.group(1)] = (p, t)
for cls in sorted(DELETE):
    if cls not in classes:
        raise SystemExit(f'{cls}: missing before deletion')
    inbound = [name for name, (_, t) in classes.items()
               if name not in DELETE and f'L{cls};' in t]
    if inbound:
        raise SystemExit(f'{cls}: external references remain: {inbound[:40]}')
for cls in sorted(DELETE):
    classes[cls][0].unlink()
    print('deleted', cls)

# Hard feature-preservation assertions.
required = [
    'com/google/android/apps/inputmethod/libs/delight5/Delight5Facilitator',
    'com/google/android/keyboard/client/delight5/Decoder',
    'com/google/android/apps/inputmethod/libs/latin5/LatinIme',
]
for cls in required:
    if not list(ROOT.glob(f'smali*/**/{cls}.smali')):
        raise SystemExit(f'required Latin5/local-AI class missing: {cls}')
for marker in ['NativeLCRunnerWrapper']:
    if not any(marker in p.read_text(errors='ignore') for p in ROOT.glob('smali*/**/*.smali')):
        raise SystemExit(f'required local feature marker missing: {marker}')

for needle in ['Lhwp;', 'Lhwn;', 'Lhwm;', 'Lhwo;', 'Lhwr;', 'Lhwq;', 'Lhwl;']:
    residual = [str(p.relative_to(ROOT)) for p in ROOT.glob('smali*/**/*.smali')
                if needle in p.read_text(errors='ignore')]
    if residual:
        raise SystemExit(f'residual {needle}: {residual[:20]}')
print('Latin5 metrics exporter physically removed; Delight5/local AI retained')
