#!/usr/bin/env python3
"""Remove the pinned Stage-23 security-provider request-statistics handoff.

Delete the reporting call, timestamp/payload collection, report-only exception
logging, and a newly unreferenced long-argument adapter. Keep provider discovery,
installation, the shared reflection utility, and native configuration unchanged.
This performs static edits only; no runtime or privacy-final claim is made.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

INPUT_SHA = '08073c39f009b7679c36fa1a4364d42fe945b755ac66062627da85a65351d401'
TARGET = 'smali_classes2/com/google/android/gms/learning/dynamite/training/InAppTrainingServiceImpl.smali'
HELPER = 'smali/qqg.smali'
EXPECTED = {
    TARGET: 'ffc3eef7086e221bde443f1606cff3f3fd5c4ed943e6271ffe3e5355885949bb',
    HELPER: '34f025a817ac8963cf5eafaed19349e131c00e93c234a7c9eedace10d20c8597',
}
METHOD_SHA = 'aae74f7540ab07c38809b31986d1ff3a29f0d82a96055dbf62199e52f6d821fd'
METHOD = re.compile(r'(?ms)^\.method[^\n]*\n.*?^\.end method')
DELETED_HELPER = 'o(J)Lqqg;'
MARKERS = ('reportRequestStats2', 'Failed to report request stats: ')


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def methods(text: str) -> dict[str, str]:
    found = METHOD.findall(text)
    out = {s.splitlines()[0].split()[-1]: s for s in found}
    require(len(found) == len(out), 'Duplicate method signature')
    return out


def label_checks(text: str) -> None:
    for body in methods(text).values():
        code = re.sub(r'"(?:\\.|[^"\\])*"', '""', body)
        code = re.sub(r'(?m)#.*$', '', code)
        declarations = re.sub(r'(?ms)^[ \t]*\.(packed-switch|sparse-switch|array-data)\b.*?^[ \t]*\.end \1[^\n]*', '', code)
        labels = re.findall(r'(?m)^[ \t]*(:\w+)[ \t]*$', declarations)
        require(len(labels) == len(set(labels)), 'Duplicate code label')
        targets = set(re.findall(r'(?<!\w):(?:cond|goto|try_start|try_end|catch|catchall|pswitch|sswitch|array)_\w+', code))
        require(targets <= set(labels), 'Unresolved label: ' + repr(targets - set(labels)))
        for match in re.finditer(r'\.catch(?:all)?(?: \S+)? \{(:\w+) \.\. (:\w+)\} (:\w+)', code):
            start, end, handler = match.groups()
            pos = {l: re.search(r'(?m)^[ \t]*' + re.escape(l) + r'[ \t]*$', code).start() for l in (start,end,handler)}
            require(pos[start] < pos[end], 'Invalid protected range')
            span = code[pos[start]:pos[end]]
            require(any(line.strip() and not line.lstrip().startswith(('.', ':')) for line in span.splitlines()), 'Empty protected range')


def transform_method(old: str) -> str:
    require(digest(old) == METHOD_SHA, 'Reporting method input drift')
    # The first uptime capture only supplies the removed report's first long.
    pattern = r'(?m)^    invoke-static \{\}, Landroid/os/SystemClock;->uptimeMillis\(\)J\n\n    move-result-wide v15\n'
    new, count = re.subn(pattern, '', old)
    require(count == 1, 'Expected one initial statistics timestamp')
    # This second initialized-state read controlled only report dispatch. The
    # first read selecting the actual provider-install route must stay intact.
    new, count = re.subn(r'(?m)(^    :cond_1\n)    sget-boolean v0, Llrz;->b:Z\n', r'\1', new)
    require(count == 1, 'Expected one reporting-only initialized-state read')
    start = re.search(r'(?m)^    if-nez v0, :cond_3$', new)
    end = re.search(r'(?m)^    :goto_5$', new)
    require(start is not None and end is not None and start.start() < end.start(), 'Reporting region not exact')
    cut = new[start.start():end.start()]
    require(all(m in cut for m in MARKERS), 'Wrong reporting region')
    require(cut.count('Lqqg;->o(J)Lqqg;') == 2, 'Wrong long-payload count')
    require('Llrz;->a(' not in cut, 'Reporting region unexpectedly includes provider installation')
    # Keep the shared constant used by subsequent retained code; give the
    # remaining installation block the same catch-all handler as before.
    replacement = '    move/from16 v22, v13\n\n    :try_start_b\n\n'
    new = new[:start.start()] + replacement + new[end.start():]
    require(not any(m in new for m in MARKERS), 'Reporting marker survived')
    return new


def apply(root: Path, report: Path, dry_run: bool = False) -> dict:
    before = {p.relative_to(root).as_posix(): p.read_text() for p in root.glob('smali*/**/*.smali')}
    require(len(before) == 21761, 'Input class count is not Stage 23')
    for p, sha in EXPECTED.items():
        require(p in before and digest(before[p]) == sha, 'Input drift: ' + p)
    require({p for p,t in before.items() if 'Lqqg;->' + DELETED_HELPER in t} == {TARGET}, 'New long-adapter consumer')
    require(sum(t.count('Lqqg;->' + DELETED_HELPER) for t in before.values()) == 2, 'Unexpected adapter call count')
    require(not any(re.search(r'const-string(?:/jumbo)?[^\n]*"(?:qqg|Lqqg;)"', t) for t in before.values()), 'Exact reflective class token needs review')
    for marker in MARKERS:
        require({p for p,t in before.items() if marker in t} == {TARGET}, 'Additional report path: ' + marker)
    hits = [m for m in methods(before[TARGET]).values() if MARKERS[0] in m]
    require(len(hits) == 1, 'Expected one reporting method')
    after = dict(before)
    after[TARGET] = before[TARGET].replace(hits[0], transform_method(hits[0]), 1)
    helper = methods(before[HELPER])[DELETED_HELPER]
    require('Ljava/lang/Long;->valueOf(J)' in helper and 'Lqqg;-><init>' in helper, 'Unexpected long-adapter body')
    after[HELPER] = before[HELPER].replace(helper, '', 1)
    changed = sorted(p for p in before if before[p] != after[p])
    require(set(changed) == set(EXPECTED), 'Unexpected edit scope')
    for path, text in after.items():
        require(not any(m in text for m in (*MARKERS, 'Lqqg;->' + DELETED_HELPER)), 'Removed reference remains: ' + path)
    for path in changed:
        label_checks(after[path])
    result = {
        'input_apk_sha256': INPUT_SHA, 'class_count_before': len(before), 'class_count_after': len(after),
        'modified_files': changed, 'unchanged_class_files': len(after) - len(changed),
        'deleted_helper_methods': {'qqg': [DELETED_HELPER]}, 'added_methods': [], 'added_classes': [], 'deleted_classes': [],
        'reporting_handoffs_removed': 1, 'report_only_uptime_captures_removed': 2,
        'before_hashes': {p: digest(before[p]) for p in changed}, 'after_hashes': {p: digest(after[p]) for p in changed},
        'net_smali_bytes_removed': sum(len(before[p].encode()) - len(after[p].encode()) for p in changed),
        'provider_installation_preserved': True, 'native_config_builder_unchanged': True,
        'runtime_tested': False, 'voice_fix_claimed': False, 'privacy_final': False, 'dry_run': dry_run,
    }
    if not dry_run:
        for path in changed:
            (root / path).write_text(after[path])
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2) + '\n')
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('root', type=Path)
    ap.add_argument('--report', type=Path, required=True)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(json.dumps(apply(args.root, args.report, args.dry_run), indent=2))


if __name__ == '__main__':
    main()
