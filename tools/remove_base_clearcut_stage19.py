#!/usr/bin/env python3
"""Exact-build physical BaseClearcutAdapter excision for Meboard Stage 19.

Input: Apktool 3.0.3 decode of Stage-18 APK SHA-256
29b41378b2cec4ec805abf9a9dc0fdbdbb8a265d1d089c4b7aa888de896c9ba8.
No no-op replacements: delete adapter/fallback/event classes and only their
branches inside shared synthetic classes. Preserve constants/register layouts
used by retained branches. Plan and validate every edit before writing anything.
This is a static-only TEST stage, not a runtime or privacy-final certification.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

EXPECTED = {'prl': {'path': 'smali/prl.smali', 'sha256': 'e5c7c6e840a8d64b30545c8c87031578c08ef4e000c0c2059e611027ead72adc'}, 'psh': {'path': 'smali/psh.smali', 'sha256': 'ea87e85d38b0cce845c2ede8fedc9eb9be92a9062f79d9f49749876d904ef479'}, 'pri': {'path': 'smali/pri.smali', 'sha256': 'a99bcda392f7eb8b26c3257e2148f01772f04a20021ff0768a398e85c0288c79'}, 'prj': {'path': 'smali/prj.smali', 'sha256': '3e6d0862db0652323018d14ce3b486d03f236aa1f22cd7ada7f6227045bbf672'}, 'prk': {'path': 'smali/prk.smali', 'sha256': '732bc5cb01ec89b02135e8aaf090aee2fbd1f7089fd6120f54723a77b0a4a0f5'}, 'prm': {'path': 'smali_classes2/prm.smali', 'sha256': '44a3f8a56ca07f91cd0e3d2f64311593421c11a60b02e2489a694b2634949404'}, 'pse': {'path': 'smali_classes2/pse.smali', 'sha256': '4e0599f6d691a8c9495ecabf376732ae54fccbe57ef73341395e99a2a2e3d154'}, 'psf': {'path': 'smali_classes2/psf.smali', 'sha256': 'c8a48c52323a323b8b7d4ae79961189806dd4f7e509230c1a1339aa1bb3d0adb'}, 'daq': {'path': 'smali_classes2/daq.smali', 'sha256': '55f4e6a26367d1e386f0f6d0236737ce4917cefbed82478b37a59fb89f0dff53'}, 'lsn': {'path': 'smali/lsn.smali', 'sha256': '5cb98de3f7797b57ad947e236dac08e33e19d2c8af157a77014a86818b00c785'}, 'mhc': {'path': 'smali/mhc.smali', 'sha256': '527c6fe61ee734da2a681469c9f4bbe6167db585aafbfa1a47d9955662d56c77'}, 'opu': {'path': 'smali/opu.smali', 'sha256': '0c09605337d16ad4acd1bd63d9faa21dff4fb8fa91d14c68b258d144924783a1'}, 'pdm': {'path': 'smali/pdm.smali', 'sha256': '4ef142aaa27802ffcfe858d9a42c4d12a59425b5a3da1a9e54a4ff50cd4c1eaa'}, 'fjr': {'path': 'smali_classes2/fjr.smali', 'sha256': '2bdaeeec984da70c03f0a860ba7566ffe531439a57451141b48e50b6dfbf6b6b'}, 'nwk': {'path': 'smali_classes2/nwk.smali', 'sha256': '2f1adfe0ae05bec5b6f3f6ebdbb149ecb1d6e9ce458c81f082beccd1f49f8f76'}, 'jdz': {'path': 'smali/jdz.smali', 'sha256': 'bdb6f25493bbb6d23a4e5e8530396ea50a83c847b37c1d2851598906d1abffbe'}, 'jea': {'path': 'smali/jea.smali', 'sha256': 'cc9d8579e3d9a3f29ea1982146a0d7fe2907228e822323ea4cc5c7d89b0ea423'}}
DELETE = ('prl', 'psh', 'pri', 'prj', 'prk', 'prm', 'pse', 'psf')
PACKED = {'daq': (2,), 'lsn': (17, 18), 'pdm': (9,), 'fjr': (12,), 'nwk': (17,)}
METHOD = re.compile(r'(?ms)^\.method[^\n]*\n.*?^\.end method')
LABEL = re.compile(r'(?m)^[ \t]*(:[\w]+)[ \t]*$')


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def remove_slice(body: str, start: int, end: int) -> str:
    """Refuse deletion of a block with a retained branch/handler targeting it."""
    removed = body[start:end]
    remaining = body[:start] + body[end:]
    for label in LABEL.findall(removed):
        require(not re.search(re.escape(label) + r'(?![\w])', remaining),
                f'retained code targets removed label {label}')
    return remaining


def prune_packed(body: str, cases: tuple[int, ...]) -> str:
    table_rx = re.compile(
        r'(?ms)(^[ \t]*(:pswitch_data_[0-9a-f]+)[ \t]*\n)'
        r'[ \t]*\.packed-switch[ \t]+(0x[0-9a-f]+)\n'
        r'(.*?)^[ \t]*\.end packed-switch')
    tables = list(table_rx.finditer(body))
    require(len(tables) == 1, 'expected exactly one packed-switch table')
    table = tables[0]
    labels = re.findall(r':pswitch_[0-9a-f]+', table[4])
    base = int(table[3], 0)
    mapping = dict(enumerate(labels, base))
    require(all(c in mapping for c in cases), 'missing reviewed switch case')
    removed_labels = {mapping[c] for c in cases}
    require(all(v not in removed_labels for k, v in mapping.items() if k not in cases),
            'deleted switch body is shared with retained case')
    # A sparse table removes the case instead of aliasing it to another feature.
    replacement = table[1] + '    .sparse-switch\n' + ''.join(
        f'        0x{k:x} -> {v}\n' for k, v in mapping.items() if k not in cases
    ) + '    .end sparse-switch'
    body = body[:table.start()] + replacement + body[table.end():]
    body, count = re.subn(
        r'(?m)^([ \t]*)packed-switch ([vp]\d+), ' + re.escape(table[2]) + r'[ \t]*$',
        r'\1sparse-switch \2, ' + table[2], body)
    require(count == 1, 'switch opcode rewrite count differs from one')
    # Compute all original case-body ranges before removing them.
    table_start = body.index(table[2])
    # The first occurrence above is the operand, so locate its declaration.
    table_start = re.search(r'(?m)^[ \t]*' + re.escape(table[2]) + r'[ \t]*$', body).start()
    code_labels = list(re.finditer(r'(?m)^[ \t]*(:pswitch_[0-9a-f]+)[ \t]*$', body[:table_start]))
    ranges = []
    for i, match in enumerate(code_labels):
        if match[1] in removed_labels:
            end = code_labels[i + 1].start() if i + 1 < len(code_labels) else table_start
            ranges.append((match.start(), end))
    require(len(ranges) == len(removed_labels), 'switch body range count mismatch')
    for start, end in reversed(ranges):
        body = remove_slice(body, start, end)
    return body


def prune_conditional(body: str, cls: str) -> str:
    if cls == 'mhc':
        # Do NOT delete const/4 v3, 0x3: retained dictation case 4 consumes v3.
        branch = '    if-eq v0, v3, :cond_5\n'
        require(body.count(branch) == 1, 'mhc selector not exact')
        body = body.replace(branch, '', 1)
        start = re.search(r'(?m)^[ \t]*:cond_5[ \t]*$', body).start()
        end = re.search(r'(?m)^[ \t]*:cond_8[ \t]*$', body).start()
        return remove_slice(body, start, end)
    selectors = {
        'jdz': ('if-eq v0, v3, :cond_2', ':cond_2'),
        'jea': ('if-eq v0, v2, :cond_0', ':cond_0'),
        'opu': ('if-eq v0, v1, :cond_1', ':cond_1'),
    }
    selector, live_label = selectors[cls]
    # The highest discriminator was the telemetry default. After its only
    # producer is deleted, let the last RETAINED case be the real fallthrough.
    # Earlier retained conditions, constants and all live case bodies stay exact.
    start_match = re.search(r'(?m)^[ \t]*' + re.escape(selector) + r'[ \t]*$', body)
    end_match = re.search(r'(?m)^[ \t]*' + re.escape(live_label) + r'[ \t]*$', body)
    require(start_match is not None and end_match is not None, f'{cls} selectors absent')
    return remove_slice(body, start_match.start(), end_match.start())


def transform(text: str, cls: str) -> str:
    methods = [m for m in METHOD.finditer(text)
               if ('Lpsh;' if cls == 'daq' else 'Lprl;') in m[0]]
    require(len(methods) == 1, f'{cls}: expected one mixed method')
    method = methods[0]
    body = (prune_packed(method[0], PACKED[cls]) if cls in PACKED
            else prune_conditional(method[0], cls))
    return text[:method.start()] + body + text[method.end():]


def validate_labels(text: str, path: str) -> None:
    for method in METHOD.findall(text):
        # Strings and comments may themselves contain colons.
        code = re.sub(r'"(?:\\.|[^"\\])*"', '""', method)
        code = re.sub(r'(?m)#.*$', '', code)
        declared = LABEL.findall(code)
        require(len(declared) == len(set(declared)), f'{path}: duplicate labels')
        targets = set(re.findall(r'(?<![\w]):(?:cond|goto|try_start|try_end|catch|catchall|pswitch|sswitch|array)_[\w]+', code))
        require(targets <= set(declared), f'{path}: unresolved labels {targets-set(declared)}')


def apply(root: Path, report: Path, dry_run: bool = False) -> dict:
    texts = {p.relative_to(root).as_posix(): p.read_text()
             for p in root.glob('smali*/**/*.smali')}
    require(len(texts) == 21770, f'wrong input class count: {len(texts)}')
    for cls, entry in EXPECTED.items():
        require(entry['path'] in texts, f'missing input: {entry["path"]}')
        require(sha(texts[entry['path']]) == entry['sha256'], f'input drift: {cls}')
    updated = dict(texts)
    for cls in (*PACKED, 'mhc', 'opu', 'jdz', 'jea'):
        path = EXPECTED[cls]['path']
        updated[path] = transform(texts[path], cls)
        validate_labels(updated[path], path)
    for cls in DELETE:
        del updated[EXPECTED[cls]['path']]
    forbidden = re.compile('|'.join(re.escape('L' + c + ';') for c in DELETE)
                           + '|BaseClearcutAdapter|GoogleKeyboardClearcutAdapter'
                           + '|ClearcutAdapterNotification.notifyClearcutReady')
    hits = [p for p,t in updated.items() if forbidden.search(t)]
    require(not hits, f'deleted descriptor/reporting residue: {hits}')
    # Reject direct reflective class-name literals as well as typed references.
    reflection = re.compile(r'const-string(?:/jumbo)?[^\n]*"(?:' + '|'.join(DELETE) + r')"')
    # Reviewed fws literals feed rpl.b() -> java.util.Locale, not reflection.
    locale_path = 'smali_classes2/fws.smali'
    require(sha(updated[locale_path]) == '2cf6877aa4cf99dca70e77c0a1cd9951fb95e347a610517413d0a1903f695d7d',
            'reviewed locale map drifted')
    require(not any(reflection.search(t) for p,t in updated.items() if p != locale_path),
            'unreviewed literal class-name match remains')
    changed = sorted(p for p in updated if updated[p] != texts[p])
    removed = sorted(set(texts)-set(updated))
    require(len(changed) == 9 and len(removed) == 8, 'unexpected delta size')
    result = {
        'input_apk_sha256': '29b41378b2cec4ec805abf9a9dc0fdbdbb8a265d1d089c4b7aa888de896c9ba8',
        'before_classes': len(texts), 'after_classes': len(updated),
        'deleted_classes': list(DELETE), 'deleted_files': removed, 'modified_files': changed,
        'unmodified_class_files': len(updated)-len(changed),
        'removed_smali_bytes': sum(len(texts[p].encode()) for p in removed),
        'net_smali_bytes_removed': sum(len(t.encode()) for t in texts.values())-sum(len(t.encode()) for t in updated.values()),
        'switch_cases_removed': {k:list(v) for k,v in PACKED.items()},
        'conditional_cases_removed': {'mhc':3,'opu':2,'jdz':3,'jea':4},
        'no_deleted_descriptor_references': True, 'no_new_classes': True,
        'no_noop_replacement': True, 'label_checks_passed': True,
        'before_hashes': {p:sha(texts[p]) for p in changed+removed},
        'after_hashes': {p:sha(updated[p]) for p in changed},
        'native_changed': False, 'manifest_changed': False, 'resources_changed': False,
        'runtime_tested': False, 'privacy_final': False,
        'dry_run': dry_run,
    }
    if not dry_run:
        for p in changed:
            (root/p).write_text(updated[p])
        for p in removed:
            (root/p).unlink()
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    try:
        apply(args.root,args.report,args.dry_run)
    except (ValueError,OSError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == '__main__':
    main()
