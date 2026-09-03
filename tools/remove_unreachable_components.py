#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path('/mnt/data/meboard_work/buildtree')
PARTS=[
'PhenotypeMetadataHolderService',
'com/google/android/gms/learning/internal/training/InAppTrainingService',
'ExampleStoreServiceMultiplexer',
'CrashResistantSwissArmyKnifeFileProvider',
'ColdStartupTraceContentProvider',
'FederatedResultHandlingService',
'WebDebugBridgeContentProvider',
'AccountRemovedBroadcastReceiver',
'PhenotypeUpdateBackgroundBroadcastReceiver',
'androidx/work/impl/diagnostics/DiagnosticsReceiver',
'com/google/android/play/core/missingsplits/PlayCoreMissingSplitsActivity',
'com/google/android/libraries/performance/primes/metrics/storage/PackageStatsCapture$PackageStatsCallback',
]
classes={}
for p in ROOT.glob('smali*/**/*.smali'):
    t=p.read_text(errors='ignore')
    m=re.search(r'^\.class[^\n]* L([^;]+);',t,re.M)
    if m: classes[m.group(1)]=(p,t)
selected=[]
for part in PARTS:
    exact=part if '/' in part and part in classes else None
    hits=[exact] if exact else [c for c in classes if part in c]
    hits=[c for c in hits if c]
    if not hits: print('not found',part); continue
    for c in hits:
        refs=[s for s,(p,t) in classes.items() if s!=c and f'L{c};' in t]
        if refs: raise SystemExit(f'{c} unexpectedly referenced by {refs[:20]}')
        selected.append(c)
for c in selected:
    classes[c][0].unlink(); print('deleted',c)
print('deleted',len(selected),'unreachable component/telemetry classes')
