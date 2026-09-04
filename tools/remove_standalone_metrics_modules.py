#!/usr/bin/env python3
"""Physically delete four standalone metrics-only module clusters.

Removes PostCorrection metrics, DailyPing, InputMethodEntry metrics, and the
DefaultCounter module while retaining the corresponding keyboard features.
The module factories, Dagger providers/interfaces, processors/helpers, and
unreachable implementations are all deleted rather than disabled.
"""
from pathlib import Path
import re

ROOT = Path('/mnt/data/meboard_work/buildtree')
EQT = ROOT / 'smali/eqt.smali'
MODULES = [
    ('E', 'ios', 'iot', 'hyy', 13, {'ios', 'ioq', 'ior', 'iot'}),
    ('X', 'nlo', 'nlp', 'mus', 6, {'nlo', 'nlq', 'nlr', 'nlp'}),
    ('ad', 'otl', 'otm', 'ogx', 6, {'otl', 'otj', 'otk', 'otm'}),
    ('ai', 'prt', 'pru', 'pks', 4, {'prt', 'prs', 'pru'}),
]


def find_class(cls: str) -> Path:
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


def remove_registry_entries(text: str) -> str:
    mm = re.search(r'(?ms)^\.method public final aI\(\)Ljava/util/Set;\n.*?^\.end method', text, re.M)
    if not mm:
        raise SystemExit('eqt.aI module registry not found')
    body = mm.group(0)
    lines = body.splitlines()
    arr = next((i for i, line in enumerate(lines) if 'new-array v11, v11, [Lpth;' in line), None)
    if arr is None:
        raise SystemExit('eqt.aI module array not found')
    wanted = {(dispatcher, case) for _, _, _, dispatcher, case, _ in MODULES}
    regs = {}
    matches = []
    current_block_start = arr + 1
    for i, line in enumerate(lines):
        s = line.strip()
        c = re.match(r'const(?:/4|/16)?\s+(v\d+),\s+(-?0x[0-9a-f]+|-?\d+)', s)
        if c:
            regs[c.group(1)] = int(c.group(2), 0)
        mv = re.match(r'move(?:/from16|/16)?\s+(v\d+),\s+(v\d+)', s)
        if mv:
            regs[mv.group(1)] = regs.get(mv.group(2))
        ctor = re.match(r'invoke-direct \{(v\d+),\s*(v\d+)\}, L([^;]+);-><init>\(I\)V', s)
        if ctor and (ctor.group(3), regs.get(ctor.group(2))) in wanted:
            obj = ctor.group(1)
            start = None
            for j in range(i, current_block_start - 1, -1):
                if re.match(rf'\s*new-instance\s+{re.escape(obj)},\s+L{re.escape(ctor.group(3))};', lines[j]):
                    start = j
                    break
            if start is None:
                raise SystemExit(f'cannot locate allocation for {ctor.group(3)} case {regs.get(ctor.group(2))}')
            matches.append([ctor.group(3), regs.get(ctor.group(2)), start, None])
        if re.match(r'\s*aput-object\s+\w+,\s+v11,\s+v23\s*$', line):
            for rec in reversed(matches):
                if rec[3] is None:
                    rec[3] = i
                    break
            current_block_start = i + 1
    found = {(x[0], x[1]) for x in matches}
    if found != wanted or len(matches) != len(wanted):
        raise SystemExit(f'registry target mismatch: wanted={sorted(wanted)}, found={sorted(found)}, records={matches}')
    if any(x[3] is None for x in matches):
        raise SystemExit(f'unterminated registry blocks: {matches}')
    for dispatcher, case, start, end in sorted(matches, key=lambda x: x[2], reverse=True):
        del lines[start:end + 1]
        print(f'eqt.aI: removed {dispatcher} discriminator {case} module factory')
    arr = next(i for i, line in enumerate(lines) if 'new-array v11, v11, [Lpth;' in line)
    stores = [i for i in range(arr + 1, len(lines)) if re.match(r'\s*aput-object\s+\w+,\s+v11,\s+v23\s*$', lines[i])]
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
        raise SystemExit('eqt.aI module count constant not found')
    print(f'eqt.aI: compacted module registry to {len(stores)} entries')
    return text[:mm.start()] + '\n'.join(lines) + text[mm.end():]


def prune_dispatcher_case(cls: str, case: int) -> None:
    p = find_class(cls)
    text = p.read_text()
    changed = 0
    for a, b, method in reversed(method_ranges(text)):
        if 'packed-switch' not in method:
            continue
        dm = re.search(r'(?ms)(^\s*:pswitch_data_[0-9a-f]+\s*\n\s*\.packed-switch\s+0x([0-9a-f]+)\s*\n)(.*?)(^\s*\.end packed-switch)', method, re.M)
        if not dm:
            continue
        base = int(dm.group(2), 16)
        labels = re.findall(r':pswitch_[0-9a-f]+', dm.group(3))
        cmap = {base + i: label for i, label in enumerate(labels)}
        if case not in cmap:
            continue
        label = cmap[case]
        data_pos = dm.start()
        code_labels = list(re.finditer(rf'(?m)^\s*{re.escape(label)}\s*$', method[:data_pos]))
        if not code_labels:
            continue
        retained = [x for x in cmap if x != case]
        replacement = cmap[min(retained, key=lambda x: abs(x - case))]
        table, n = re.subn(rf'(?m)^(\s*){re.escape(label)}\s*$', rf'\1{replacement}', dm.group(3), count=1)
        if n != 1:
            raise SystemExit(f'{cls}: failed to rewrite switch table case {case}')
        method = method[:dm.start(3)] + table + method[dm.end(3):]
        data_pos = method.rfind(dm.group(1).splitlines()[0].strip())
        code_labels = list(re.finditer(rf'(?m)^\s*{re.escape(label)}\s*$', method[:data_pos]))
        start = code_labels[-1].start()
        nxt = re.search(r'(?m)^\s*:pswitch_[0-9a-f]+\s*$', method[code_labels[-1].end():data_pos])
        end = code_labels[-1].end() + nxt.start() if nxt else data_pos
        segment = method[start:end]
        outside = method[:start] + method[end:data_pos]
        preserve = end
        for lm in re.finditer(r'(?m)^\s*(:[A-Za-z0-9_]+)\s*$', segment):
            internal = lm.group(1)
            if internal.startswith(':pswitch_'):
                continue
            if re.search(rf'(?<![A-Za-z0-9_]){re.escape(internal)}(?![A-Za-z0-9_])', outside):
                preserve = min(preserve, start + lm.start())
        method = method[:start] + method[preserve:]
        text = text[:a] + method + text[b:]
        changed += 1
    if changed != 2:
        raise SystemExit(f'{cls}: expected two factory/definition branches for case {case}, removed {changed}')
    p.write_text(text)
    print(f'{cls}: physically removed discriminator {case} from create/definition methods')


def remove_eqt_provider(text: str, method_name: str, ret_cls: str, iface: str) -> str:
    text, n = re.subn(rf'(?m)^\.implements L{re.escape(iface)};\n', '', text, count=1)
    if n != 1:
        raise SystemExit(f'eqt: missing implements {iface}')
    pat = re.compile(rf'(?ms)^\.method public final {re.escape(method_name)}\(\)L{re.escape(ret_cls)};\n.*?^\.end method\n?')
    text, n = pat.subn('', text, count=1)
    if n != 1:
        raise SystemExit(f'eqt: provider {method_name}(){ret_cls} not uniquely found')
    print(f'eqt: removed provider {method_name}()L{ret_cls}; and interface {iface}')
    return text


text = remove_registry_entries(EQT.read_text())
for method_name, ret_cls, iface, dispatcher, case, _ in MODULES:
    text = remove_eqt_provider(text, method_name, ret_cls, iface)
EQT.write_text(text)
for _, _, _, dispatcher, case, _ in MODULES:
    prune_dispatcher_case(dispatcher, case)

all_delete = set().union(*(entry[5] for entry in MODULES))
classes = {}
for p in ROOT.glob('smali*/**/*.smali'):
    t = p.read_text(errors='ignore')
    m = re.search(r'^\.class[^\n]* L([^;]+);', t, re.M)
    if m:
        classes[m.group(1)] = (p, t)
for cls in sorted(all_delete):
    if cls not in classes:
        raise SystemExit(f'{cls}: missing before deletion')
    inbound = [name for name, (_, t) in classes.items() if name not in all_delete and f'L{cls};' in t]
    if inbound:
        raise SystemExit(f'{cls}: external references remain: {inbound[:40]}')
for cls in sorted(all_delete):
    classes[cls][0].unlink()
    print('deleted', cls)
for needle in ['Lios;', 'Lnlo;', 'Lotl;', 'Lprt;', 'Liot;', 'Lnlp;', 'Lotm;', 'Lpru;']:
    residual = []
    for p in ROOT.glob('smali*/**/*.smali'):
        if needle in p.read_text(errors='ignore'):
            residual.append(str(p.relative_to(ROOT)))
    if residual:
        raise SystemExit(f'residual {needle}: {residual[:20]}')
print('standalone metrics-only module clusters physically removed')
