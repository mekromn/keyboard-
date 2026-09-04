#!/usr/bin/env python3
"""Physically remove detached Latin and Latin-common metrics processors.

These processors no longer have application registration roots. Their remaining
references are self-contained helper classes and six discriminator branches in
shared java.util.function synthetic classes. Core Latin IME, Delight5, language
models, dictionaries, setup UI, permissions, and feature implementations remain.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path('/mnt/data/meboard_work/buildtree')
SMALI_ROOTS = [ROOT / n for n in ('smali', 'smali_classes2', 'smali_classes3', 'smali_classes4')]
DELETE = {'evm', 'evn', 'hyu', 'hyv', 'hyw', 'hyx'}
EXPECTED_INBOUND = {
    'evm': {'evl', 'evn'},
    'evn': {'evm'},
    'hyu': {'evm', 'hyv'},
    'hyv': {'exj', 'hyw'},
    'hyw': {'hyv'},
    'hyx': {'hyv'},
}
EXPECTED_CASE_PRODUCERS = {
    'evl': {0: {'evn': 1}, 2: {'evn': 1}, 3: {'evm': 1}},
    'exj': {9: {'hyv': 1}, 10: {'hyv': 1}, 11: {'hyv': 1}},
}
METHOD_SIGNATURES = {
    'evl': r'^\.method public final accept\(Ljava/lang/Object;\)V$',
    'exj': r'^\.method public final apply\(Ljava/lang/Object;\)Ljava/lang/Object;$',
}
MARKERS = {
    'evm': 'LatinMetricsProcessor',
    'evn': 'LatinMetricsProcessorHelper',
    'hyu': 'LatinCommonCountersUtils',
    'hyv': 'LatinCommonMetricsProcessor',
    'hyw': 'LatinCommonMetricsProcessorHelper',
    'hyx': 'LatinCommonMetricsUtils',
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


def rg_files(needle: str) -> list[Path]:
    run = subprocess.run(
        ['rg', '-l', '-F', needle, *map(str, SMALI_ROOTS), '--glob', '*.smali'],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if run.returncode not in (0, 1):
        raise SystemExit(run.stderr)
    return [Path(line) for line in run.stdout.splitlines() if line]


def inbound(name: str) -> set[str]:
    own = find_class(name)
    return {declared_name(path) for path in rg_files(f'L{name};') if path != own}


def constructor_case_sites(target: str) -> dict[int, dict[str, int]]:
    result: dict[int, dict[str, int]] = {}
    call_token = f'L{target};-><init>'
    for path in rg_files(call_token):
        owner = declared_name(path)
        regs: dict[str, int | None] = {}
        for line in path.read_text(errors='ignore').splitlines():
            text = line.strip()
            if text.startswith('.method'):
                regs = {}
                continue
            match = re.match(
                r'const(?:/4|/16|/high16)?\s+([vp]\d+),\s+'
                r'(-?0x[0-9a-f]+|-?\d+)',
                text,
            )
            if match:
                try:
                    regs[match.group(1)] = int(match.group(2), 0)
                except ValueError:
                    regs[match.group(1)] = None
                continue
            match = re.match(
                r'move(?:-object)?(?:/from16|/16)?\s+([vp]\d+),\s+([vp]\d+)',
                text,
            )
            if match:
                regs[match.group(1)] = regs.get(match.group(2))
                continue
            if call_token not in text:
                continue
            args_match = re.search(r'\{([^}]*)\}', text)
            if not args_match:
                raise SystemExit(f'{path}: constructor args missing: {text}')
            raw = args_match.group(1)
            if '..' in raw:
                first, last = [item.strip() for item in raw.split('..')]
                a = re.fullmatch(r'([vp])(\d+)', first)
                b = re.fullmatch(r'([vp])(\d+)', last)
                if not a or not b or a.group(1) != b.group(1):
                    raise SystemExit(f'{path}: unsupported range args: {raw}')
                args = [f'{a.group(1)}{i}' for i in range(int(a.group(2)), int(b.group(2)) + 1)]
            else:
                args = [item.strip() for item in raw.split(',') if item.strip()]
            if not args:
                raise SystemExit(f'{path}: empty constructor args')
            value = regs.get(args[-1])
            if value is None:
                continue
            owners = result.setdefault(value, {})
            owners[owner] = owners.get(owner, 0) + 1
    return result


def method_ranges(text: str):
    result = []
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
        result.append((start, end, text[start:end]))
        pos = end
    return result


def prune_cases(path: Path, method_signature: str, removed: set[int]) -> None:
    text = path.read_text()
    matching = [item for item in method_ranges(text) if re.match(method_signature, item[2].splitlines()[0])]
    if len(matching) != 1:
        raise SystemExit(f'{path.name}: expected one target method, got {len(matching)}')
    method_start, method_end, body = matching[0]
    data_matches = list(re.finditer(
        r'(?ms)^\s*(:pswitch_data_[0-9a-f]+)\s*\n'
        r'\s*\.packed-switch\s+(-?0x[0-9a-f]+|-?\d+)\s*\n'
        r'(.*?)^\s*\.end packed-switch',
        body,
        re.M,
    ))
    if len(data_matches) != 1:
        raise SystemExit(f'{path.name}: expected one packed switch, got {len(data_matches)}')
    dm = data_matches[0]
    base = int(dm.group(2), 0)
    labels = re.findall(r':pswitch_[0-9a-f]+', dm.group(3))
    mapping = {base + idx: label for idx, label in enumerate(labels)}
    if removed - set(mapping):
        raise SystemExit(f'{path.name}: missing cases {sorted(removed - set(mapping))}')
    retained = [case for case in mapping if case not in removed]
    data = dm.group(3)
    for case in sorted(removed):
        old = mapping[case]
        replacement = mapping[min(retained, key=lambda item: abs(item - case))]
        data, count = re.subn(
            rf'(?m)^(\s*){re.escape(old)}\s*$',
            rf'\1{replacement}',
            data,
            count=1,
        )
        if count != 1:
            raise SystemExit(f'{path.name}: case {case} table count {count}')
    body = body[:dm.start(3)] + data + body[dm.end(3):]

    table_pos = body.rfind(dm.group(1))
    removals = []
    for case in sorted(removed):
        label = mapping[case]
        code_labels = list(re.finditer(rf'(?m)^\s*{re.escape(label)}\s*$', body[:table_pos]))
        if len(code_labels) != 1:
            raise SystemExit(f'{path.name}: case {case} code label count {len(code_labels)}')
        start = code_labels[0].start()
        next_case = re.search(
            r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',
            body[code_labels[0].end():table_pos],
        )
        end = code_labels[0].end() + next_case.start() if next_case else table_pos
        segment = body[start:end]
        outside = body[:start] + body[end:table_pos]
        preserve = end
        for label_match in re.finditer(r'(?m)^\s*(:[A-Za-z0-9_]+)\s*$', segment):
            inner = label_match.group(1)
            if inner.startswith(':pswitch_'):
                continue
            if re.search(
                rf'(?<![A-Za-z0-9_]){re.escape(inner)}(?![A-Za-z0-9_])',
                outside,
            ):
                preserve = min(preserve, start + label_match.start())
        if preserve <= start:
            raise SystemExit(f'{path.name}: case {case} empty removal')
        removals.append((start, preserve, case, len(segment)))
    for start, end, case, size in sorted(removals, reverse=True):
        body = body[:start] + body[end:]
        print(f'{path.name}: removed metrics discriminator case {case} ({size} chars)')
    text = text[:method_start] + body + text[method_end:]
    path.write_text(text)


paths = {name: find_class(name) for name in DELETE}
for name, marker in MARKERS.items():
    if marker not in paths[name].read_text(errors='ignore'):
        raise SystemExit(f'{name}: marker {marker!r} missing')
for name, expected in EXPECTED_INBOUND.items():
    actual = inbound(name)
    if actual != expected:
        raise SystemExit(f'{name}: inbound {sorted(actual)} != {sorted(expected)}')
for processor in ('evm', 'hyv'):
    calls = rg_files(f'L{processor};-><init>')
    if calls:
        raise SystemExit(
            f'{processor}: detached processor unexpectedly constructed by '
            f'{[str(path.relative_to(ROOT)) for path in calls]}'
        )
for dispatcher, expected in EXPECTED_CASE_PRODUCERS.items():
    actual = constructor_case_sites(dispatcher)
    for case, owners in expected.items():
        if actual.get(case) != owners:
            raise SystemExit(
                f'{dispatcher} case {case}: constructor producers '
                f'{actual.get(case)} != {owners}'
            )

prune_cases(find_class('evl'), METHOD_SIGNATURES['evl'], set(EXPECTED_CASE_PRODUCERS['evl']))
prune_cases(find_class('exj'), METHOD_SIGNATURES['exj'], set(EXPECTED_CASE_PRODUCERS['exj']))

bytes_removed = sum(path.stat().st_size for path in paths.values())
for name in sorted(paths):
    paths[name].unlink()
    print('deleted detached Latin metrics class', name)
for name in sorted(paths):
    hits = rg_files(f'L{name};')
    if hits:
        raise SystemExit(f'{name}: residual refs {[str(p.relative_to(ROOT)) for p in hits[:20]]}')
for marker in MARKERS.values():
    hits = rg_files(marker)
    if hits:
        raise SystemExit(f'{marker}: residual refs {[str(p.relative_to(ROOT)) for p in hits[:20]]}')

print(f'physically removed detached Latin metrics: {len(paths)} classes / {bytes_removed} smali bytes')
