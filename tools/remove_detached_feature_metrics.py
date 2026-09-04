#!/usr/bin/env python3
"""Physically remove detached Undo, FreeCursor, and companion-widget metrics islands.

The feature implementations remain elsewhere. These six classes are metrics
processors/helpers whose app registration roots were removed earlier; each has
only one dead shared-synthetic factory/callback edge left.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path('/mnt/data/meboard_work/buildtree')
SMALI_ROOTS = [ROOT / n for n in ('smali', 'smali_classes2', 'smali_classes3', 'smali_classes4')]
CLUSTERS = {
    'undo': {
        'classes': {'kbl', 'kbm'},
        'processor': 'kbl',
        'helper': 'kbm',
        'marker': 'UndoMetricsProcessorHelper',
        'dispatcher': 'cuu',
        'case': 5,
        'branch_markers': {'Lkbl;', 'Lkbm;'},
        'expected_inbound': {'kbl': {'cuu', 'kbm'}, 'kbm': {'cuu'}},
    },
    'freecursor': {
        'classes': {'oan', 'oao'},
        'processor': 'oan',
        'helper': 'oao',
        'marker': 'FreeCursorMetricsProcessorHelper',
        'dispatcher': 'ipd',
        'case': 14,
        'branch_markers': {'Loan;', 'Loao;'},
        'expected_inbound': {'oan': {'ipd', 'oao'}, 'oao': {'ipd'}},
    },
    'widget': {
        'classes': {'nan', 'nao'},
        'processor': 'nan',
        'helper': 'nao',
        'marker': 'WidgetMetricsProcessorHelper',
        'dispatcher': 'fol',
        'case': 8,
        'branch_markers': {'Lnan;'},
        'expected_inbound': {'nan': {'fol', 'nao'}, 'nao': {'nan'}},
    },
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
        raise SystemExit(f'{path}: no class declaration')
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


def prune_dispatch_case(path: Path, case: int, required_markers: set[str]) -> None:
    text = path.read_text()
    hits = []
    for method_start, method_end, body in method_ranges(text):
        for dm in re.finditer(
            r'(?ms)^\s*(:pswitch_data_[0-9a-f]+)\s*\n'
            r'\s*\.packed-switch\s+(-?0x[0-9a-f]+|-?\d+)\s*\n'
            r'(.*?)^\s*\.end packed-switch',
            body,
            re.M,
        ):
            base = int(dm.group(2), 0)
            labels = re.findall(r':pswitch_[0-9a-f]+', dm.group(3))
            mapping = {base + idx: label for idx, label in enumerate(labels)}
            if case not in mapping:
                continue
            label = mapping[case]
            table_pos = dm.start()
            code_labels = list(re.finditer(rf'(?m)^\s*{re.escape(label)}\s*$', body[:table_pos]))
            if not code_labels:
                continue
            start = code_labels[-1].start()
            next_case = re.search(
                r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',
                body[code_labels[-1].end():table_pos],
            )
            end = code_labels[-1].end() + next_case.start() if next_case else table_pos
            segment = body[start:end]
            if all(marker in segment for marker in required_markers):
                hits.append((method_start, method_end, body, dm, mapping, start, end, segment))
    if len(hits) != 1:
        details = [(h[4].get(case), sorted(m for m in required_markers if m in h[7])) for h in hits]
        raise SystemExit(f'{path.name}: expected one case {case} target branch, got {len(hits)} {details}')

    method_start, method_end, body, dm, mapping, start, end, segment = hits[0]
    label = mapping[case]
    retained = [item for item in mapping if item != case]
    replacement = mapping[min(retained, key=lambda item: abs(item - case))]
    data = dm.group(3)
    data, count = re.subn(
        rf'(?m)^(\s*){re.escape(label)}\s*$',
        rf'\1{replacement}',
        data,
        count=1,
    )
    if count != 1:
        raise SystemExit(f'{path.name}: case {case} table entry count {count}')
    body = body[:dm.start(3)] + data + body[dm.end(3):]

    table_pos = body.rfind(dm.group(1))
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
    for lm in re.finditer(r'(?m)^\s*(:[A-Za-z0-9_]+)\s*$', segment):
        internal = lm.group(1)
        if internal.startswith(':pswitch_'):
            continue
        if re.search(
            rf'(?<![A-Za-z0-9_]){re.escape(internal)}(?![A-Za-z0-9_])',
            outside,
        ):
            preserve = min(preserve, start + lm.start())
    if preserve <= start:
        raise SystemExit(f'{path.name}: case {case} empty branch removal')
    body = body[:start] + body[preserve:]
    text = text[:method_start] + body + text[method_end:]
    path.write_text(text)
    print(f'{path.name}: physically removed dead discriminator case {case} ({len(segment)} chars)')


all_remove = set().union(*(cfg['classes'] for cfg in CLUSTERS.values()))
paths = {name: find_class(name) for name in all_remove}
for label, cfg in CLUSTERS.items():
    processor_text = paths[cfg['processor']].read_text(errors='ignore')
    helper_text = paths[cfg['helper']].read_text(errors='ignore')
    if '.implements Lpqw;' not in processor_text:
        raise SystemExit(f"{label}: {cfg['processor']} is not a metrics processor")
    if '.super Lpqh;' not in helper_text:
        raise SystemExit(f"{label}: {cfg['helper']} is not a metrics helper")
    if cfg['marker'] not in helper_text:
        raise SystemExit(f"{label}: marker {cfg['marker']} missing")
    for name, expected in cfg['expected_inbound'].items():
        actual = inbound(name)
        if actual != expected:
            raise SystemExit(f'{label}/{name}: inbound {sorted(actual)} != {sorted(expected)}')
    ctor_sites = rg_files(f"L{cfg['processor']};-><init>")
    if ctor_sites:
        raise SystemExit(
            f"{label}: detached processor unexpectedly constructed by "
            f"{[str(p.relative_to(ROOT)) for p in ctor_sites]}"
        )

for cfg in CLUSTERS.values():
    prune_dispatch_case(
        find_class(cfg['dispatcher']),
        cfg['case'],
        cfg['branch_markers'],
    )

bytes_removed = sum(path.stat().st_size for path in paths.values())
for name in sorted(paths):
    paths[name].unlink()
    print('deleted detached metrics class', name)

for name in sorted(paths):
    refs = rg_files(f'L{name};')
    if refs:
        raise SystemExit(f'{name}: residual refs {[str(p.relative_to(ROOT)) for p in refs[:20]]}')
for cfg in CLUSTERS.values():
    refs = rg_files(cfg['marker'])
    if refs:
        raise SystemExit(f"{cfg['marker']}: residual refs {[str(p.relative_to(ROOT)) for p in refs[:20]]}")

print(
    f'physically removed detached Undo/FreeCursor/widget metrics: '
    f'{len(paths)} classes / {bytes_removed} smali bytes'
)
