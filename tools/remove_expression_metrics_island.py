#!/usr/bin/env python3
"""Physically remove detached expression/emoji metrics processors.

The application module-registry roots for these processors were removed earlier.
This pass proves the remaining classes form an isolated metrics-only island,
removes their shared synthetic callbacks, and then deletes the classes.
"""
from pathlib import Path
import re

ROOT = Path('/mnt/data/meboard_work/buildtree')
CLUSTER = {'gqo', 'gqp', 'gqq', 'gqr', 'gqv', 'gqw'}
EXPECTED_MARKERS = {
    'gqp': 'EmojiMetricsProcessorHelper',
    'gqq': 'ExpressionMetricsProcessor',
    'gqr': 'ExpressionMetricsProcessorHelper',
    'gqv': 'ExpressionSimpleCountersMetricsProcessor',
    'gqw': 'ExpressionSimpleCountersMetricsProcessorHelper',
}


def find_class(cls: str) -> Path:
    hits = list(ROOT.glob(f'smali*/**/{cls}.smali'))
    if len(hits) != 1:
        raise SystemExit(f'{cls}: expected one class file, got {hits}')
    return hits[0]


paths = {c: find_class(c) for c in CLUSTER}
for cls, marker in EXPECTED_MARKERS.items():
    if marker not in paths[cls].read_text(errors='ignore'):
        raise SystemExit(f'{cls}: expected marker {marker!r} missing')

# The only edge from outside this metrics island is fhj's failure callback,
# which is instantiated exclusively by gqq. Every other external edge is fatal.
for cls in sorted(CLUSTER):
    refs = []
    needle = f'L{cls};'
    for path in ROOT.glob('smali*/**/*.smali'):
        if needle in path.read_text(errors='ignore') and path.stem not in CLUSTER:
            refs.append(str(path.relative_to(ROOT)))
    allowed = {'smali_classes2/fhj.smali'} if cls == 'gqq' else set()
    if set(refs) != allowed:
        raise SystemExit(
            f'{cls}: unexpected external refs: {refs}; allowed={sorted(allowed)}'
        )

FHJ = ROOT / 'smali_classes2/fhj.smali'
text = FHJ.read_text()
REMOVE = {11, 12}


def method_ranges(source: str):
    result = []
    pos = 0
    while True:
        match = re.search(r'^\.method[^\n]*\n', source[pos:], re.M)
        if not match:
            break
        start = pos + match.start()
        end = source.find('\n.end method', pos + match.end())
        if end < 0:
            raise SystemExit('fhj: unterminated method')
        end += len('\n.end method')
        result.append((start, end, source[start:end]))
        pos = end
    return result


def prune_switch(body: str):
    data_match = re.search(
        r'(?ms)(^\s*:pswitch_data_0\s*\n'
        r'\s*\.packed-switch\s+0x([0-9a-f]+)\s*\n)'
        r'(.*?)'
        r'(^\s*\.end packed-switch)',
        body,
        re.M,
    )
    if not data_match:
        return body, 0

    base = int(data_match.group(2), 16)
    labels = re.findall(r':pswitch_[0-9a-f]+', data_match.group(3))
    case_labels = {base + index: label for index, label in enumerate(labels)}
    if REMOVE & set(case_labels) != REMOVE:
        raise SystemExit(f'fhj switch missing cases: have={sorted(case_labels)}')

    retained = [case for case in case_labels if case not in REMOVE]
    data = data_match.group(3)
    for case in sorted(REMOVE):
        old_label = case_labels[case]
        replacement = case_labels[min(retained, key=lambda item: abs(item - case))]
        data, count = re.subn(
            rf'(?m)^(\s*){re.escape(old_label)}\s*$',
            rf'\1{replacement}',
            data,
            count=1,
        )
        if count != 1:
            raise SystemExit(f'fhj case {case}: switch entry not uniquely found')

    body = body[:data_match.start(3)] + data + body[data_match.end(3):]
    data_pos = body.rfind(':pswitch_data_0')
    removals = []
    for case in sorted(REMOVE):
        label = case_labels[case]
        matches = list(
            re.finditer(rf'(?m)^\s*{re.escape(label)}\s*$', body[:data_pos])
        )
        if not matches:
            raise SystemExit(f'fhj case {case}: code label {label} missing')
        start = matches[-1].start()
        next_label = re.search(
            r'(?m)^\s*:pswitch_[0-9a-f]+\s*$',
            body[matches[-1].end():data_pos],
        )
        end = (
            matches[-1].end() + next_label.start()
            if next_label
            else data_pos
        )

        segment = body[start:end]
        outside = body[:start] + body[end:data_pos]
        preserve_from = end
        for internal in re.finditer(
            r'(?m)^\s*(:[A-Za-z0-9_]+)\s*$', segment
        ):
            internal_label = internal.group(1)
            if internal_label.startswith(':pswitch_'):
                continue
            if re.search(
                rf'(?<![A-Za-z0-9_]){re.escape(internal_label)}'
                rf'(?![A-Za-z0-9_])',
                outside,
            ):
                preserve_from = min(preserve_from, start + internal.start())
        removals.append((start, preserve_from, case))

    for start, end, case in sorted(removals, reverse=True):
        if end <= start:
            raise SystemExit(f'fhj case {case}: empty branch removal')
        body = body[:start] + body[end:]
    return body, len(removals)


changed_methods = 0
removed_branches = 0
for start, end, body in reversed(method_ranges(text)):
    if 'packed-switch' not in body:
        continue
    replacement, count = prune_switch(body)
    if count:
        text = text[:start] + replacement + text[end:]
        changed_methods += 1
        removed_branches += count
if changed_methods != 2 or removed_branches != 4:
    raise SystemExit(
        f'fhj: expected 2 methods / 4 branch bodies, '
        f'got {changed_methods}/{removed_branches}'
    )
FHJ.write_text(text)

for cls, path in paths.items():
    path.unlink()
    print('deleted metrics-only class', cls)

for needle in [
    'Lgqo;', 'Lgqp;', 'Lgqq;', 'Lgqr;', 'Lgqv;', 'Lgqw;',
    'ExpressionMetricsProcessor.java',
    'ExpressionSimpleCountersMetricsProcessor',
    'EmojiMetricsProcessorHelper',
]:
    hits = []
    for path in ROOT.glob('smali*/**/*.smali'):
        if needle in path.read_text(errors='ignore'):
            hits.append(str(path.relative_to(ROOT)))
    if hits:
        raise SystemExit(f'residual {needle}: {hits[:20]}')

print('expression/emoji telemetry processor island physically removed')
