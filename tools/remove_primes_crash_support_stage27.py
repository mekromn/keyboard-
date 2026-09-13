#!/usr/bin/env python3
"""Delete nine detached Primes crash-report-support classes from pinned Stage 26.
No surviving class, native library, resource, or configuration is edited. This
is physical dead-code removal, not proof of absent network traffic or a voice fix.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
INPUT_SHA='acd77999d2654af314fbb4fc7b248f986084471564b2a0185dffd26d2d621dd8'
EXPECTED={'uec': {'path': 'smali/uec.smali', 'sha256': '58a5d83ae0175fd04eb07948c75384ebba8aa54bc770fdd9d1bb413db5d2acf1', 'inbound': ['Luai;', 'Ludx;', 'Luec;', 'Lued;'], 'bytes': 5118, 'methods': 3}, 'ued': {'path': 'smali/ued.smali', 'sha256': 'def49d0125a9a2bfc0453024fe5007a7da7c5ad0b2db8a501e62feed6ed70fa5', 'inbound': ['Lued;'], 'bytes': 1725, 'methods': 3}, 'uai': {'path': 'smali/uai.smali', 'sha256': 'dea14d71357fa781ee701dd952f72eea13895f8dcc706f210f91a496ac8f7be7', 'inbound': ['Luai;'], 'bytes': 1470, 'methods': 3}, 'udx': {'path': 'smali/udx.smali', 'sha256': '84725bebf9e9cfcd07367887d8748840bb190b3ae5003ebaa1684effd0e8cd01', 'inbound': ['Ludx;'], 'bytes': 1365, 'methods': 3}, 'uag': {'path': 'smali/uag.smali', 'sha256': 'aedb12e625355c37b69e8cb66f541bdc2202277230399bf2495f40ef9771d889', 'inbound': ['Luag;'], 'bytes': 3137, 'methods': 3}, 'uaf': {'path': 'smali/uaf.smali', 'sha256': '8b2ee9e087b0293d42495f344ce73ac344df51756d22528bc43d0807e72959d3', 'inbound': ['Luaf;', 'Luag;', 'Luaq;'], 'bytes': 1225, 'methods': 3}, 'uae': {'path': 'smali/uae.smali', 'sha256': '6bc27090bc9f725746c7477fbb5f5066d7804deabee2ec4f222efd2117f999aa', 'inbound': ['Luae;', 'Luag;', 'Luaq;'], 'bytes': 1225, 'methods': 3}, 'uad': {'path': 'smali/uad.smali', 'sha256': '0d26c7b3e532877f1110f881108da5ea63082a8815ae63ebdd084452103cd410', 'inbound': ['Luad;', 'Luae;', 'Luaf;', 'Luag;', 'Luaq;'], 'bytes': 2067, 'methods': 2}, 'uaq': {'path': 'smali/uaq.smali', 'sha256': '7e23f2b0eff184483b0de64c0bc14520745de6dfe8b95f52e03a4a08aebcfa11', 'inbound': ['Luag;', 'Luaq;'], 'bytes': 1681, 'methods': 3}}
MARKERS=('primes/crash','com/google/android/libraries/performance/primes/metrics/crash/CrashMetricFactory','CrashMetricFactory.java')


def require(ok:bool, why:str)->None:
    if not ok: raise ValueError(why)


def apply(root:Path, report:Path, dry_run:bool=False)->dict:
    texts={p.relative_to(root).as_posix():p.read_text() for p in root.glob('smali*/**/*.smali')}
    require(len(texts)==21754,'Wrong Stage-26 input class count')
    targets={v['path'] for v in EXPECTED.values()}
    names={p:re.search(r'^\.class[^\n]* (L[^;]+;)',t,re.M)[1] for p,t in texts.items()}
    for cls,entry in EXPECTED.items():
        path=entry['path'];require(path in texts,'Target absent: '+path)
        require(hashlib.sha256(texts[path].encode()).hexdigest()==entry['sha256'],'Input drift: '+path)
        incoming={names[p] for p,t in texts.items() if 'L'+cls+';' in t}
        require(incoming==set(entry['inbound']),'Unexpected typed-reference graph: '+cls)
        require(incoming<={'L'+c+';' for c in EXPECTED},'Retained typed ingress: '+cls)
    exact=re.compile(r'const-string(?:/jumbo)?[^\n]*"(?:'+'|'.join([*EXPECTED,*('L'+n+';' for n in EXPECTED)])+r')"')
    require(not any(exact.search(t) for t in texts.values()),'Exact reflective class-name literal needs review')
    for marker in MARKERS:
        owners={p for p,t in texts.items() if marker in t}
        require(bool(owners) and owners<=targets,'Marker outside deleted cluster: '+marker)
    result={'input_sha256':INPUT_SHA,'classes_before':len(texts),'classes_after':len(texts)-len(targets),
        'deleted_classes':sorted(EXPECTED),'deleted_files':sorted(targets),'modified_surviving_files':[],
        'classes_added':0,'methods_added':0,'removed_smali_bytes':sum(len(texts[p].encode()) for p in targets),
        'removed_method_definitions':sum(len(re.findall(r'^\.method',texts[p],re.M)) for p in targets),
        'closed_inbound_graph':{n:e['inbound'] for n,e in EXPECTED.items()},
        'native_modified':False,'voice_fix_claimed':False,'runtime_tested':False,'privacy_final':False,'dry_run':dry_run}
    if not dry_run:
        for path in targets:(root/path).unlink()
    report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(result,indent=2)+'\n')
    return result


def main()->None:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    p.add_argument('--report',type=Path,required=True);p.add_argument('--dry-run',action='store_true')
    a=p.parse_args();print(json.dumps(apply(a.root,a.report,a.dry_run),indent=2))
if __name__=='__main__':main()
