#!/usr/bin/env python3
"""Remove active Mozc Clearcut/timing reporting sinks without touching Mozc input.

The Stage-16 working tree still registers MozcProcessorProvider, which creates:
  * MozcClearcutMetricsProcessor (ibi) and helper (ibj)
  * Mozc timing processor (ibn)

This exact-build pass removes that module root, its Dagger interface/provider,
and the Mozc-only branch of the shared kbt notification listener. Candidate UI,
Japanese conversion, dictionaries, transliteration, GenAI emoji behavior, and
the Undo notification branch in kbt are retained. Event producer enums are left
for a separately reviewed producer-removal pass; after this pass they have no
Mozc reporting processor registered.
"""
from __future__ import annotations

import re
from pathlib import Path

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

    regs: dict[str, int | None] = {}
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
            start = next(
                (j for j in range(i, arr, -1)
                 if re.match(rf'\s*new-instance\s+{re.escape(obj)},\s+L{re.escape(dispatcher)};', lines[j])),
                None,
            )
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
    stores = [
        i for i in range(arr + 1, len(lines))
        if re.match(r'\s*aput-object\s+\w+,\s+v11,\s+v23\s*$', lines[i])
    ]
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
    path = find(cls)
    text = path.read_text()
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
            table, count = re.subn(
                rf'(?m)^(\s*){re.escape(label)}\s*$',
                rf'\1{replacement}',
                dm.group(3),
                count=1,
            )
            if count != 1:
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
    path.write_text(text)
    print(f'{cls}: removed discriminator {case} Mozc processor-provider branch x{changed}')


def replace_method(text: str, header: str, replacement: str, description: str) -> str:
    pattern = re.compile(rf'(?ms)^\.method[^\n]*{re.escape(header)}\n.*?^\.end method\n?')
    text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise SystemExit(f'{description}: replaced {count}')
    return text


# Exact structural guard before modifying anything.
checks = {
    'ibi': 'com/google/android/apps/inputmethod/libs/mozc/metrics/MozcClearcutMetricsProcessor',
    'ibj': 'com/google/android/apps/inputmethod/libs/mozc/metrics/MozcClearcutMetricsProcessorHelper',
    'ibl': 'MozcProcessorProvider.onCreate',
}
for cls, marker in checks.items():
    if marker not in find(cls).read_text(errors='ignore'):
        raise SystemExit(f'{cls}: expected marker missing: {marker}')
if 'const-class p0, Libo;' not in find('ibn').read_text(errors='ignore'):
    raise SystemExit('ibn: Mozc timing enum provider marker missing')

# Remove module root and Dagger provider interface.
text = remove_registry_factory(EQT.read_text(), 'hyy', 4)
text, count = re.subn(r'(?m)^\.implements Libm;\n', '', text, count=1)
if count != 1:
    raise SystemExit('eqt implements ibm missing')
text, count = re.subn(r'(?ms)^\.method public final z\(\)Libl;\n.*?^\.end method\n?', '', text, count=1)
if count != 1:
    raise SystemExit('eqt z()Libl provider missing')
EQT.write_text(text)
print('eqt: removed Mozc processor provider z() and ibm interface')
prune_case('hyy', 4, 'ibl', 2)

# Preserve Undo behavior in the shared notification listener while deleting the
# Mozc-only constructor and receive/clear branches.
kbt = find('kbt')
text = kbt.read_text()
text, count = re.subn(r'(?m)^\.field private final synthetic b:I\n\n?', '', text, count=1)
if count != 1:
    raise SystemExit('kbt discriminator field missing')
text, count = re.subn(
    r'(?ms)^\.method public constructor <init>\(Libi;I\)V\n.*?^\.end method\n?',
    '', text, count=1,
)
if count != 1:
    raise SystemExit('kbt Mozc constructor missing')
# The retained kbg constructor keeps its binary signature but no longer stores a
# synthetic discriminator, because only the Undo implementation remains.
text, count = re.subn(r'(?m)^\s*iput p2, p0, Lkbt;->b:I\n\n?', '', text, count=1)
if count != 1:
    raise SystemExit('kbt retained-constructor discriminator write missing')

undo_clear = '''.method public final synthetic dT(Ljava/lang/Class;)V
    .locals 0

    const-string p0, "UndoStripNotification$Listener.onClear"

    invoke-static {p0}, Landroid/os/Trace;->beginSection(Ljava/lang/String;)V

    invoke-static {}, Landroid/os/Trace;->endSection()V

    return-void
.end method

'''
text = replace_method(text, 'dT(Ljava/lang/Class;)V', undo_clear, 'kbt.dT')
undo_receive = '''.method public final synthetic dU(Lpyj;)V
    .locals 2

    const-string v0, "UndoStripNotification$Listener.onReceive"

    invoke-static {v0}, Landroid/os/Trace;->beginSection(Ljava/lang/String;)V

    :try_start_0
    check-cast p1, Lkbu;

    iget-object v0, p0, Lkbt;->c:Ljava/lang/Object;

    invoke-static {v0, p1}, Labol;->k(Ljava/lang/Object;Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_2

    iget-boolean v0, p1, Lkbu;->a:Z

    iget-object v1, p0, Lkbt;->a:Ljava/lang/Object;

    if-eqz v0, :cond_0

    check-cast v1, Lmis;

    invoke-virtual {v1}, Lmis;->t()V

    goto :goto_0

    :cond_0
    check-cast v1, Lmis;

    invoke-virtual {v1}, Lmis;->s()V

    :goto_0
    iput-object p1, p0, Lkbt;->c:Ljava/lang/Object;

    :cond_2
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    invoke-static {}, Landroid/os/Trace;->endSection()V

    return-void

    :catchall_0
    move-exception p0

    invoke-static {}, Landroid/os/Trace;->endSection()V

    throw p0
.end method
'''
text = replace_method(text, 'dU(Lpyj;)V', undo_receive, 'kbt.dU')
for forbidden in ('Libi;', 'Libg;', 'MozcCandidateListVisualMetricNotification'):
    if forbidden in text:
        raise SystemExit(f'kbt Mozc listener residue remains: {forbidden}')
for required in ('Lkbg;', 'Lkbu;', 'UndoStripNotification$Listener.onReceive'):
    if required not in text:
        raise SystemExit(f'kbt Undo behavior missing after pruning: {required}')
kbt.write_text(text)
print('kbt: removed Mozc visual-metric listener branch; retained Undo listener')

DELETE = {'ibf', 'ibi', 'ibj', 'ibl', 'ibm', 'ibn'}
classes: dict[str, tuple[Path, str]] = {}
class_rx = re.compile(r'^\.class[^\n]* L([^;]+);', re.M)
for path in ROOT.glob('smali*/**/*.smali'):
    content = path.read_text(errors='ignore')
    match = class_rx.search(content)
    if match:
        classes[match.group(1)] = (path, content)
for cls in sorted(DELETE):
    if cls not in classes:
        raise SystemExit(f'{cls}: missing before deletion')
    inbound = [
        name for name, (_, content) in classes.items()
        if name not in DELETE and f'L{cls};' in content
    ]
    if inbound:
        raise SystemExit(f'{cls}: external references remain: {inbound[:40]}')
for cls in sorted(DELETE):
    classes[cls][0].unlink()
    print('deleted', cls)

# Hard feature-preservation and sink-removal gates.
for keep in (
    'com/google/android/apps/inputmethod/libs/mozc/ime/SimpleJapaneseIme',
    'kbg', 'kbt', 'kbu', 'hfa', 'hzv', 'hzu', 'hzt',
):
    if not list(ROOT.glob(f'smali*/**/{keep}.smali')):
        raise SystemExit(f'required Japanese/Undo feature class missing: {keep}')
for needle in ('MozcClearcutMetricsProcessor', 'MozcClearcutMetricsProcessorHelper', 'MozcProcessorProvider.onCreate'):
    residual = [
        str(path.relative_to(ROOT)) for path in ROOT.glob('smali*/**/*.smali')
        if needle in path.read_text(errors='ignore')
    ]
    if residual:
        raise SystemExit(f'residual Mozc reporting sink marker {needle}: {residual[:20]}')
print('Mozc Clearcut/timing reporting sinks physically removed; Japanese and Undo features retained')
