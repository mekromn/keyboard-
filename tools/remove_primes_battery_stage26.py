#!/usr/bin/env python3
"""Pinned Stage-25 -> Stage-26 deletion of a detached Primes battery reporter.
No surviving class is edited, and no stub or forced flag is introduced. The
native literal guard in verify_primes_battery_apk_stage26 must also pass.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
INPUT_SHA='085171de9c84d7b1001ac956a1fe7f5addbedba4910f5a8bb06e70989299dfda'
EXPECTED = {
  "smali/tys.smali": "59909e4cfc465ac7aec068cf0014bc7fcd701bbe690351b3a32805c36f724f1e",
  "smali/tyr.smali": "dd22b7b4e107a9e3734eab2785109bea17bcc43354c8bd89630978fceb2ef92c",
  "smali_classes3/tyq.smali": "1609368685f080525dbd4de93263989e9d9e2208273fe6836c64e4a37e729396",
  "smali/tzb.smali": "46d0dc3ea01bceabe1b246dc9af6942ec24295f667142c1059d82e25d15aebab"
}
GRAPH={
 'tys':{'smali/tys.smali'},
 'tyr':{'smali/tyr.smali','smali/tys.smali','smali_classes3/tyq.smali'},
 'tyq':{'smali/tyr.smali','smali_classes3/tyq.smali'},
 'tzb':{'smali/tys.smali','smali/tzb.smali'},
}
MARKERS=('primes.battery.snapshot','com/google/android/libraries/performance/primes/metrics/battery/BatteryMetricServiceImpl')

def require(ok:bool,message:str)->None:
    if not ok:raise ValueError(message)

def apply(root:Path,report:Path,dry_run:bool=False)->dict:
    texts={p.relative_to(root).as_posix():p.read_text() for p in root.glob('smali*/**/*.smali')}
    require(len(texts)==21758,'Input class count differs from Stage 25')
    for path,digest in EXPECTED.items():
        require(path in texts and hashlib.sha256(texts[path].encode()).hexdigest()==digest,'Input drift: '+path)
    for cls,expected in GRAPH.items():
        actual={p for p,t in texts.items() if 'L'+cls+';' in t}
        require(actual==expected,'Changed reference graph: '+cls)
    strings=re.compile(r'const-string(?:/jumbo)?[^\n]*"(?:'+ '|'.join(GRAPH)+r'|L(?:'+ '|'.join(GRAPH)+r');)"')
    require(not any(strings.search(t) for t in texts.values()),'Potential reflective name requires review')
    for marker in MARKERS:
        owners={p for p,t in texts.items() if marker in t}
        require(bool(owners) and owners<=EXPECTED.keys(),'Unexpected marker owner: '+marker)
    # No typing/local AI/timing/transport class needs rewriting for this cluster.
    remaining={p:t for p,t in texts.items() if p not in EXPECTED}
    require(not any(any('L'+c+';' in t for c in GRAPH) for t in remaining.values()),'Surviving reference to deleted type')
    # Scan XML/JSON/config text too. Short language tags alone are not class names.
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix not in {'.xml','.json','.txt','.cfg','.properties'}:continue
        require(not any('L'+c+';' in p.read_text(errors='replace') for c in GRAPH),'Non-smali class descriptor: '+str(p))
    result={'input_apk_sha256':INPUT_SHA,'classes_before':len(texts),'classes_after':len(remaining),
      'deleted_files':sorted(EXPECTED),'deleted_classes':sorted(GRAPH),'modified_surviving_classes':[],
      'unchanged_surviving_class_files':len(remaining),'added_classes':[],
      'removed_smali_bytes':sum(len(texts[p].encode()) for p in EXPECTED),
      'removed_method_definitions':sum(len(re.findall(r'^\.method ',texts[p],re.M)) for p in EXPECTED),
      'expected_reference_graph':{c:sorted(v) for c,v in GRAPH.items()},'before_hashes':EXPECTED,
      'removed_markers':list(MARKERS),'dry_run':dry_run,'native_modified':False,'runtime_tested':False,'privacy_final':False}
    if not dry_run:
        for p in EXPECTED:(root/p).unlink()
    report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(result,indent=2)+'\n')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--report',type=Path,required=True);p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    print(json.dumps(apply(a.root,a.report,a.dry_run),indent=2))
if __name__=='__main__':main()
