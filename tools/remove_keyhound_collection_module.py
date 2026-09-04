#!/usr/bin/env python3
"""Physically remove Gboard's hidden Keyhound input-data collection module.

Keyhound is not the voice, handwriting, Mozc, or Latin input engine. It is a
metrics/private-command module that subscribes to those engines, serializes
input actions/audio-command metadata/stylus gestures, encrypts dumps, and grants
a content URI to a requesting package. This patch removes the module,
processors, collectors, provider, shared synthetic branches, and resource path
while leaving the observed feature engines intact.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path('/mnt/data/meboard_work/buildtree')
SMALI_ROOTS = [ROOT / n for n in ('smali', 'smali_classes2', 'smali_classes3', 'smali_classes4')]
DELETE = {
    'htc', 'htd', 'hte', 'htf', 'htg', 'hth', 'hti',
    'htj', 'htk', 'htl', 'htn', 'hto',
    'com/google/android/apps/inputmethod/libs/keyhound/InputActionFileProvider',
}
EXPECTED_INBOUND = {
    'htc': {'hal', 'hth'},
    'htd': {'hte', 'htm'},
    'hte': {'exn', 'ffd', 'htf', 'htg', 'hth', 'htm'},
    'htf': {'hte'},
    'htg': {'hth'},
    'hth': {'hal', 'htg'},
    'hti': {'htf', 'htg', 'hto'},
    'htj': {'hpn', 'htg', 'hth', 'htk'},
    'htk': {'htj'},
    'htl': {'gab', 'htf', 'htg', 'hth', 'htk', 'hto'},
    'htn': {'exn', 'hth', 'htm', 'hto'},
    'hto': {'htn'},
    'com/google/android/apps/inputmethod/libs/keyhound/InputActionFileProvider': set(),
}


def find_class(name: str) -> Path:
    hits = []
    for root in SMALI_ROOTS:
        hits.extend(root.rglob(name + '.smali'))
    if len(hits) != 1:
        raise SystemExit(f'{name}: expected one class, got {hits}')
    return hits[0]


def declared_name(path: Path) -> str:
    match = re.search(r'^\.class[^\n]* L([^;]+);', path.read_text(errors='ignore'), re.M)
    if not match:
        raise SystemExit(f'{path}: missing class declaration')
    return match.group(1)


def rg_files(needle: str, include_xml: bool = False) -> list[Path]:
    roots = [*map(str, SMALI_ROOTS)]
    globs = ['--glob', '*.smali']
    if include_xml:
        roots.append(str(ROOT / 'AndroidManifest.xml'))
        roots.append(str(ROOT / 'res'))
        globs += ['--glob', '*.xml']
    run = subprocess.run(
        ['rg', '-l', '-F', needle, *roots, *globs],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if run.returncode not in (0, 1):
        raise SystemExit(run.stderr)
    return [Path(line) for line in run.stdout.splitlines() if line]


def inbound(name: str) -> set[str]:
    own = find_class(name)
    return {declared_name(path) for path in rg_files(f'L{name};') if path != own}


def method_ranges(text: str):
    out = []
    pos = 0
    while True:
        match = re.search(r'^\.method[^\n]*\n', text[pos:], re.M)
        if not match:
            break
        start = pos + match.start()
        end = text.find('\n.end method', pos + match.end())
        if end < 0:
            raise SystemExit('unterminated smali method')
        end += len('\n.end method')
        out.append((start, end, text[start:end]))
        pos = end
    return out


def prune_cases(path: Path, cases: set[int], expected_methods: int) -> None:
    text = path.read_text()
    changed_methods = 0
    removed_branches = 0
    for method_start, method_end, body in reversed(method_ranges(text)):
        switches = list(re.finditer(
            r'(?ms)^\s*(:pswitch_data_[0-9a-f]+)\s*\n'
            r'\s*\.packed-switch\s+(-?0x[0-9a-f]+|-?\d+)\s*\n'
            r'(.*?)^\s*\.end packed-switch',
            body,
            re.M,
        ))
        if len(switches) > 1:
            raise SystemExit(f'{path.name}: unsupported multiple packed switches in one method')
        if not switches:
            continue
        dm = switches[0]
        base = int(dm.group(2), 0)
        labels = re.findall(r':pswitch_[0-9a-f]+', dm.group(3))
        mapping = {base + index: label for index, label in enumerate(labels)}
        active = cases & set(mapping)
        if not active:
            continue
        concrete = {}
        table_pos = dm.start()
        for case in active:
            label = mapping[case]
            code = list(re.finditer(rf'(?m)^\s*{re.escape(label)}\s*$', body[:table_pos]))
            if code:
                if labels.count(label) != 1:
                    raise SystemExit(f'{path.name}: case {case} shares live label {label}')
                concrete[case] = label
        if not concrete:
            continue
        retained = [case for case in mapping if case not in concrete]
        if not retained:
            raise SystemExit(f'{path.name}: refusing to remove every switch case')
        data = dm.group(3)
        for case, label in sorted(concrete.items()):
            replacement = mapping[min(retained, key=lambda item: abs(item - case))]
            data, count = re.subn(
                rf'(?m)^(\s*){re.escape(label)}\s*$',
                rf'\1{replacement}',
                data,
                count=1,
            )
            if count != 1:
                raise SystemExit(f'{path.name}: table rewrite case {case} count {count}')
        body = body[:dm.start(3)] + data + body[dm.end(3):]
        table_pos = body.rfind(dm.group(1))
        removals = []
        for case, label in sorted(concrete.items()):
            code = list(re.finditer(rf'(?m)^\s*{re.escape(label)}\s*$', body[:table_pos]))
            if len(code) != 1:
                raise SystemExit(f'{path.name}: code label {label} count {len(code)}')
            start = code[0].start()
            next_case = re.search(
                r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',
                body[code[0].end():table_pos],
            )
            end = code[0].end() + next_case.start() if next_case else table_pos
            segment = body[start:end]
            outside = body[:start] + body[end:table_pos]
            preserve = end
            for inner_match in re.finditer(r'(?m)^\s*(:[A-Za-z0-9_]+)\s*$', segment):
                inner = inner_match.group(1)
                if inner.startswith(':pswitch_'):
                    continue
                if re.search(
                    rf'(?<![A-Za-z0-9_]){re.escape(inner)}(?![A-Za-z0-9_])',
                    outside,
                ):
                    preserve = min(preserve, start + inner_match.start())
            if preserve <= start:
                raise SystemExit(f'{path.name}: case {case} empty removal')
            removals.append((start, preserve, case, len(segment)))
        for start, end, case, size in sorted(removals, reverse=True):
            body = body[:start] + body[end:]
            print(f'{path.name}: removed dead Keyhound discriminator {case} ({size} chars)')
            removed_branches += 1
        text = text[:method_start] + body + text[method_end:]
        changed_methods += 1
    if changed_methods != expected_methods:
        raise SystemExit(
            f'{path.name}: expected {expected_methods} changed methods, got {changed_methods} '
            f'({removed_branches} branches)'
        )
    path.write_text(text)


def remove_method(path: Path, header_regex: str, description: str) -> None:
    text = path.read_text()
    pattern = re.compile(rf'(?ms)^\.method[^\n]*{header_regex}\n.*?^\.end method\n?')
    text, count = pattern.subn('', text, count=1)
    if count != 1:
        raise SystemExit(f'{description}: expected one method, got {count}')
    path.write_text(text)
    print('removed', description)


def remove_registry_entry() -> None:
    path = find_class('eqt')
    lines = path.read_text().splitlines()
    method_start = next(i for i, line in enumerate(lines) if line.startswith('.method public final aI()Ljava/util/Set;'))
    method_end = next(i for i in range(method_start + 1, len(lines)) if lines[i] == '.end method')
    method = lines[method_start:method_end + 1]
    array_line = next(i for i, line in enumerate(method) if re.search(r'new-array\s+v11,\s+v11,\s+\[Lpth;', line))

    registers: dict[str, int | None] = {}
    candidates = []
    for index, line in enumerate(method[array_line + 1:], array_line + 1):
        text = line.strip()
        match = re.match(r'const(?:/4|/16)?\s+(v\d+),\s+(-?0x[0-9a-f]+|-?\d+)', text)
        if match:
            registers[match.group(1)] = int(match.group(2), 0)
            continue
        match = re.match(r'move(?:/from16|/16)?\s+(v\d+),\s+(v\d+)', text)
        if match:
            registers[match.group(1)] = registers.get(match.group(2))
            continue
        match = re.match(r'invoke-direct \{(v\d+),\s*(v\d+)\}, Lhal;-><init>\(I\)V', text)
        if match and registers.get(match.group(2)) == 13:
            candidates.append((index, match.group(1)))
    if len(candidates) != 1:
        raise SystemExit(f'eqt: expected one hal(13) module factory, got {candidates}')
    invoke_line, obj = candidates[0]
    start = next(
        i for i in range(invoke_line, array_line, -1)
        if re.match(rf'\s*new-instance\s+{re.escape(obj)},\s+Lhal;', method[i])
    )
    end = next(
        i for i in range(invoke_line + 1, len(method))
        if re.match(rf'\s*aput-object\s+{re.escape(obj)},\s+v11,\s+v23\s*$', method[i])
    )
    original_count = sum(
        1 for line in method[array_line + 1:]
        if re.match(r'\s*aput-object\s+\w+,\s+v11,\s+v23\s*$', line)
    )
    del method[start:end + 1]

    rebuilt = []
    index = 0
    for line in method:
        if re.match(r'\s*aput-object\s+\w+,\s+v11,\s+v23\s*$', line):
            while rebuilt and re.match(r'\s*const/16\s+v23,\s+0x[0-9a-f]+\s*$', rebuilt[-1]):
                rebuilt.pop()
            rebuilt.append(f'    const/16 v23, 0x{index:x}')
            rebuilt.append(line)
            index += 1
        else:
            rebuilt.append(line)
    method = rebuilt
    if index != original_count - 1:
        raise SystemExit(f'eqt: registry count {index} != {original_count - 1}')
    array_line = next(i for i, line in enumerate(method) if re.search(r'new-array\s+v11,\s+v11,\s+\[Lpth;', line))
    for i in range(array_line - 1, max(-1, array_line - 16), -1):
        if re.match(r'\s*const/16\s+v11,\s+0x[0-9a-f]+\s*$', method[i]):
            method[i] = f'    const/16 v11, 0x{index:x}'
            break
    else:
        raise SystemExit('eqt: registry length constant missing')
    lines[method_start:method_end + 1] = method
    path.write_text('\n'.join(lines) + '\n')
    print(f'eqt: removed Keyhound module factory; registry now {index} entries')


def patch_htm() -> None:
    path = find_class('htm')
    remove_method(path, r'constructor <init>\(Lhte;\[BLjava/lang/String;I\)V', 'htm InputAction dump constructor')
    remove_method(path, r'constructor <init>\(Lhtn;\[BLjava/lang/String;I\)V', 'htm voice dump constructor')
    text = path.read_text()
    call = re.search(r'(?ms)^\.method public final synthetic call\(\)Ljava/lang/Object;\n.*?^\.end method', text, re.M)
    if not call:
        raise SystemExit('htm call() missing')
    body = call.group(0)
    body, count0 = re.subn(r'(?m)^\s*if-eqz v1, :cond_12\n', '', body, count=1)
    body, count1 = re.subn(r'(?m)^\s*if-eq v1, v2, :cond_11\n', '', body, count=1)
    if (count0, count1) != (1, 1):
        raise SystemExit(f'htm dead discriminator jumps {(count0, count1)}')
    dead = re.search(r'(?ms)^\s*:cond_11\s*$.*?(?=^\s*:pswitch_data_0\s*$)', body, re.M)
    if not dead or 'Lhte;' not in dead.group(0) or 'Lhtn;' not in dead.group(0):
        raise SystemExit('htm Keyhound return branches changed')
    body = body[:dead.start()] + body[dead.end():]
    text = text[:call.start()] + body + text[call.end():]
    path.write_text(text)
    print('htm: removed InputAction/voice dump callables; SAPI/AI callables retained')


for name, expected in EXPECTED_INBOUND.items():
    actual = inbound(name)
    if actual != expected:
        raise SystemExit(f'{name}: inbound {sorted(actual)} != {sorted(expected)}')

remove_registry_entry()
prune_cases(find_class('hal'), {13}, 2)
prune_cases(find_class('gab'), {18}, 4)
prune_cases(find_class('exn'), {6, 7}, 2)
prune_cases(find_class('ffd'), {16, 17}, 1)
prune_cases(find_class('hpn'), {12}, 1)
remove_method(find_class('exn'), r'constructor <init>\(Lhte;I\)V', 'exn InputAction failure callback constructor')
remove_method(find_class('exn'), r'constructor <init>\(Lhtn;I\)V', 'exn voice failure callback constructor')
patch_htm()

manifest = ROOT / 'AndroidManifest.xml'
manifest_text = manifest.read_text()
provider_pattern = re.compile(
    r'(?ms)\s*<provider[^>]*android:name="com\.google\.android\.apps\.inputmethod\.libs\.keyhound\.InputActionFileProvider"[^>]*>.*?</provider>'
)
manifest_text, count = provider_pattern.subn('', manifest_text, count=1)
if count != 1:
    raise SystemExit(f'InputActionFileProvider manifest count {count}')
manifest.write_text(manifest_text)

resource = ROOT / 'res/xml/input_action_path.xml'
if not resource.is_file():
    raise SystemExit('input_action_path.xml missing')
resource.unlink()
public = ROOT / 'res/values/public.xml'
public_text = public.read_text()
public_text, count = re.subn(
    r'(?m)^\s*<public type="xml" name="input_action_path" id="0x[0-9a-f]+" />\n?',
    '',
    public_text,
    count=1,
)
if count != 1:
    raise SystemExit(f'input_action_path public resource count {count}')
public.write_text(public_text)

paths = {name: find_class(name) for name in DELETE}
bytes_removed = sum(path.stat().st_size for path in paths.values())
for name in sorted(paths):
    paths[name].unlink()
    print('deleted Keyhound class', name)

for name in sorted(paths):
    refs = rg_files(f'L{name};', include_xml=True)
    if refs:
        raise SystemExit(f'{name}: residual refs {[str(path.relative_to(ROOT)) for path in refs[:20]]}')
for marker in (
    'InputActionFileProvider', '.inputactionprovider', '@xml/input_action_path',
    'GET_INPUT_ACTION', 'GET_DICTATION_AUDIO', 'GET_SCRIBE_DATA', 'GET_MOZC_COMMAND',
    'VoiceKeyhoundMetricsProcessor', 'StylusKeyhoundMetricsProcessor',
    'InputActionMetricsProcessor',
):
    refs = rg_files(marker, include_xml=True)
    if refs:
        raise SystemExit(f'{marker}: residual active refs {[str(path.relative_to(ROOT)) for path in refs[:20]]}')

print(
    f'Keyhound collection/export module physically removed: '
    f'{len(paths)} classes / {bytes_removed} smali bytes; feature engines retained'
)
