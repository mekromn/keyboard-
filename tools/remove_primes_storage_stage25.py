#!/usr/bin/env python3
"""Pinned Stage-24 physical Primes storage reporter removal; no native edits.

Deletes the closed service/worker/traversal cluster and its unused factory
constructor. The mixed factory retains every case 0..6 unchanged. Its former
reporting default now rejects unsupported selectors rather than returning a
no-op or accidentally constructing an unrelated provider. Runtime untested.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

INPUT_SHA = 'd7c77f87c45eca6a91f7c5bdfcc0667f287c87f09c57890563609a5376bb5d46'
FACTORY = 'smali/tgh.smali'
PRODUCER = 'smali/pli.smali'
DELETED = {'udo': 'smali/udo.smali', 'udn': 'smali_classes3/udn.smali', 'udh': 'smali_classes3/udh.smali'}
EXPECTED = {
 FACTORY: '6f082842cba66b6f6b998a79a693626e49c7f5760f10abc8442954edac0f4037',
 DELETED['udo']: 'ddd1e2448e06462ce6c564322c45ec23400bed809f5713a85fd8a772486c4ea2',
 DELETED['udn']: '48f970dd7be3a55ebde97f03f1646f3cb15202f6fc85856eff1bd86438203f9f',
 DELETED['udh']: '48bb6979f20ec6507c8ff19ccfb13efc0c793bb7f7466e5414c10d064e6dbadc',
 PRODUCER: 'f270933ef49a6795bad5262c07a490055eb9e7fb0cc3ef5dc095afca75c11700',
}
CTOR = '<init>(Laals;Laals;Laals;Laals;Laals;Laals;Laals;I[S)V'
LIVE_CTOR = '<init>(Ltgg;Laals;Laals;Laals;Laals;Laals;Laals;I)V'
MARKERS = ('primes.packageMetric.lastSendTime',
 'com/google/android/libraries/performance/primes/metrics/storage/PackageStatsCaptureO',
 'com/google/android/libraries/performance/primes/metrics/storage/DirStatsCapture')
METHOD = re.compile(r'(?ms)^\.method[^\n]*\n.*?^\.end method')


def check(ok: bool, why: str) -> None:
    if not ok: raise ValueError(why)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def methods(text: str) -> dict[str, str]:
    found = METHOD.findall(text)
    result = {m.splitlines()[0].split()[-1]: m for m in found}
    check(len(result) == len(found), 'duplicate method signature')
    return result


def transform(text: str) -> str:
    mm = methods(text)
    check(CTOR in mm, 'reviewed unused constructor missing')
    check('iput p8, p0, Ltgh;->g:I' in mm[CTOR], 'constructor discriminator changed')
    old = mm['iM()Ljava/lang/Object;']
    switch = re.search(r'(?m)^    packed-switch v0, :pswitch_data_0$', old)
    first = re.search(r'(?m)^    :pswitch_0$', old)
    check(switch is not None and first is not None and switch.end() < first.start(), 'factory block missing')
    region = old[switch.end():first.start()]
    check(region.count('new-instance v3, Ludo;') == 1, 'not the storage factory region')
    check('return-object v3' in region and not re.search(r'(?m)^\s*:\w+', region), 'unexpected control flow')
    rejection = '''

    new-instance v0, Ljava/lang/UnsupportedOperationException;
    const-string v1, "Unsupported provider selector"
    invoke-direct {v0, v1}, Ljava/lang/UnsupportedOperationException;-><init>(Ljava/lang/String;)V
    throw v0

'''
    new = old[:switch.end()] + rejection + old[first.start():]
    text = text.replace(old, new, 1).replace(mm[CTOR], '', 1)
    check('Ludo;' not in text, 'reporter construction survives')
    return text


def apply(root: Path, report: Path, dry_run: bool = False) -> dict:
    before = {p.relative_to(root).as_posix(): p.read_text() for p in root.glob('smali*/**/*.smali')}
    check(len(before) == 21761, 'input class count differs from Stage 24')
    for path, sha in EXPECTED.items():
        check(path in before and digest(before[path]) == sha, 'input drift: ' + path)
    allowed = {
     'tgh': {FACTORY, PRODUCER},
     'udo': {FACTORY, DELETED['udo'], DELETED['udn']},
     'udn': {DELETED['udo'], DELETED['udn']},
     'udh': {DELETED['udh'], DELETED['udn']},
    }
    for cls, paths in allowed.items():
        actual = {p for p,t in before.items() if 'L'+cls+';' in t}
        check(actual == paths, f'new typed dependency for {cls}: {actual ^ paths}')
    check(not any('Ltgh;->'+CTOR in t for t in before.values()), 'unused factory constructor gained a caller')
    check(before[PRODUCER].count('Ltgh;-><init>') == 4 and
          before[PRODUCER].count('Ltgh;->'+LIVE_CTOR) == 4, 'unexpected factory constructors')
    exact = re.compile(r'const-string(?:/jumbo)?[^\n]*"(?:udo|udn|udh|tgh|Ludo;|Ludn;|Ludh;|Ltgh;)"')
    check(not any(exact.search(t) for t in before.values()), 'reflective literal needs review')
    for marker in MARKERS:
        check({p for p,t in before.items() if marker in t} == {DELETED['udn']}, 'another marker owner: '+marker)
    after = dict(before)
    after[FACTORY] = transform(before[FACTORY])
    for path in DELETED.values(): del after[path]
    banned = ['L'+c+';' for c in DELETED] + ['Ltgh;->'+CTOR, *MARKERS]
    check(not any(any(b in t for b in banned) for t in after.values()), 'removed descriptor or marker survives')
    changed = sorted(p for p in after if after[p] != before[p])
    removed = sorted(set(before)-set(after))
    check(changed == [FACTORY] and set(removed) == set(DELETED.values()), 'unexpected delta')
    result = {
     'input_apk_sha256': INPUT_SHA, 'classes_before':len(before), 'classes_after':len(after),
     'deleted_classes':list(DELETED), 'deleted_files':removed, 'modified_files':changed,
     'unchanged_class_files':len(after)-len(changed), 'deleted_constructor':CTOR,
     'removed_factory_default':'Primes storage-metrics service construction',
     'unexpected_selector_behavior':'UnsupportedOperationException; no no-op or feature substitution',
     'added_classes':[], 'added_methods':[],
     'removed_smali_bytes':sum(len(before[p].encode()) for p in removed),
     'net_smali_bytes_removed':sum(len(t.encode()) for t in before.values())-sum(len(t.encode()) for t in after.values()),
     'before_hashes':{p:digest(before[p]) for p in changed+removed},
     'after_hashes':{p:digest(after[p]) for p in changed},
     'native_modified':False, 'voice_fix_claimed':False, 'runtime_tested':False, 'privacy_final':False, 'dry_run':dry_run,
    }
    if not dry_run:
        (root/FACTORY).write_text(after[FACTORY])
        for path in removed: (root/path).unlink()
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2)+'\n')
    return result


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('root',type=Path);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    print(json.dumps(apply(a.root,a.report,a.dry_run),indent=2))

if __name__=='__main__':main()
