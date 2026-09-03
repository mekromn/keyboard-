#!/usr/bin/env python3
from pathlib import Path
import re, shutil, xml.etree.ElementTree as ET

ROOT=Path('/mnt/data/meboard_work/decoded/base')
DENS=Path('/mnt/data/meboard_work/decoded/density')
OLD='com.google.android.inputmethod.latin'
NEW='com.mekromn.meboard'
ANDROID='{http://schemas.android.com/apk/res/android}'

# Merge density assets without replacing base values/public tables.
for src in (DENS/'res').iterdir():
    if src.name in {'values'}:
        continue
    dst=ROOT/'res'/src.name
    if src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        for f in src.iterdir():
            if f.is_file():
                out=dst/f.name
                if f.suffix=='.xml':
                    txt=f.read_text().replace('APKTOOL_DUMMY_0x','APKTOOL_RENAMED_0x')
                    out.write_text(txt)
                else:
                    shutil.copy2(f,out)

# Fuse optional user-facing native engines; Brella/TensorFlow intentionally excluded.
import zipfile
for apk,libname in [
    (Path('/mnt/data/meboard_work/input/split_dictation_feature_split.apk'),'lib/arm64-v8a/libdictation_jni.so'),
    (Path('/mnt/data/meboard_work/input/split_tenoranimation_feature_split.apk'),'lib/arm64-v8a/libtenoranimation_jni.so'),
]:
    with zipfile.ZipFile(apk) as z:
        if libname in z.namelist():
            out=ROOT/libname
            out.parent.mkdir(parents=True,exist_ok=True)
            out.write_bytes(z.read(libname))

# Manifest: rebase identity and physically remove registered telemetry/training/debug/report roots.
ET.register_namespace('android','http://schemas.android.com/apk/res/android')
tree=ET.parse(ROOT/'AndroidManifest.xml'); root=tree.getroot()
root.set('package',NEW)
for a in ['coreApp',ANDROID+'requiredSplitTypes',ANDROID+'splitTypes']:
    root.attrib.pop(a,None)

# Any authority/custom permission/self URI containing the old app id must be unique for coexistence.
for e in root.iter():
    for k,v in list(e.attrib.items()):
        if OLD in v: e.set(k,v.replace(OLD,NEW))

app=root.find('application')
remove_name_parts=[
    'PhenotypeMetadataHolderService',
    'InAppTrainingService','InAppJobService',
    'ExampleStoreServiceMultiplexer','SpeechPrecomputedFeatureExampleStoreService','NWPSanityCheckEvalExampleStoreService',
    'ImageFeedbackActivity','DecoderStateReportActivity','QualityBugReportActivity',
    'CrashResistantSwissArmyKnifeFileProvider',
    'FeatureSplitDebugActivity','FeatureSplitMultiprocessMetricsService',
    'ColdStartupTraceContentProvider','LocalComputationResultHandlingService','FederatedResultHandlingService',
    'WebDebugBridgeContentProvider','LifeboatReceiver',
    'AccountRemovedBroadcastReceiver','PhenotypeUpdateBackgroundBroadcastReceiver',
    'DiagnosticsReceiver','PlayCoreMissingSplitsActivity',
]
remove_meta_parts=[
    'phenotype.registration','phenotype.heterodyne',
    'android.net.http.EnableTelemetry','com.android.vending.splits',
    'FirebaseDynamicLinkRegistrar',
]
for parent in [root,app]:
    if parent is None: continue
    for child in list(parent):
        name=child.get(ANDROID+'name','')
        if any(x in name for x in remove_name_parts):
            parent.remove(child); continue
        if child.tag=='meta-data' and any(x in name for x in remove_meta_parts):
            parent.remove(child)

tree.write(ROOT/'AndroidManifest.xml',encoding='utf-8',xml_declaration=True)

# Rebrand visible/default strings and self package literals throughout decoded text.
for p in ROOT.rglob('*'):
    if not p.is_file(): continue
    if p.suffix not in {'.smali','.xml','.txt','.json','.properties','.yml'}: continue
    try: s=p.read_text()
    except UnicodeDecodeError: continue
    ns=s.replace(OLD,NEW).replace('com/google/android/inputmethod/latin','com/mekromn/meboard')
    if p.name=='strings.xml':
        ns=ns.replace('>Gboard<','>Meboard<').replace(' Gboard ',' Meboard ').replace('Gboard','Meboard')
    if ns!=s: p.write_text(ns)

# Remove the LatinApp metrics-factory startup block physically, while preserving outer trace cleanup.
lat=ROOT/'smali/com/google/android/apps/inputmethod/latin/LatinApp.smali'
s=lat.read_text()
start=s.index('    :cond_7\n    :goto_5\n    const-string v0, "LatinApp.initializeMetricsFactories"')
catch=s.index('    :catchall_5\n',start)
replacement='''    :cond_7\n    :goto_5\n    :try_end_a\n    .catchall {:try_start_a .. :try_end_a} :catchall_5\n\n    invoke-static {}, Landroid/os/Trace;->endSection()V\n\n    return-void\n\n'''
s=s[:start]+replacement+s[catch:]
lat.write_text(s)

# Remove telemetry/training/report/debug module providers from the generated module registry and compact it.
# These are actual aI() registry positions in this exact Gboard 18.0.3 build.
REMOVE={
    0,4,13,34,35,75,99,102,117,128,133,134,135,137,144,145,158,176,200,
    205,211,222,224,225,231,241,245,248,251,260,261,262,266,268,271,273,275,
    276,280,281,282,283,284,285,
}
eqt=ROOT/'smali/eqt.smali'; text=eqt.read_text(); lines=text.splitlines()
mi=next(i for i,l in enumerate(lines) if l.startswith('.method public final aI()Ljava/util/Set;'))
me=next(i for i in range(mi+1,len(lines)) if lines[i]=='.end method')
method=lines[mi:me+1]
for i,l in enumerate(method):
    if l.strip()=='.locals 23': method[i]='    .locals 24'; break
arr_i=None
for i,l in enumerate(method):
    if 'new-array v11, v11, [Lpth;' in l:
        arr_i=i; break
if arr_i is None: raise SystemExit('aI module array not found')
kept_count=0x122-len(REMOVE)
for j in range(arr_i-1,max(-1,arr_i-8),-1):
    if re.search(r'const/16 v11, 0x122',method[j]):
        method[j]=f'    const/16 v11, 0x{kept_count:x}'
        break
else: raise SystemExit('aI module array length const not found')
aputs=[]
for i in range(arr_i+1,len(method)):
    if re.match(r'\s*aput-object\s+\w+,\s+v11,\s+\w+',method[i]):
        aputs.append(i)
if len(aputs)!=0x122: raise SystemExit(f'expected 290 module array stores, got {len(aputs)}')
blocks=[]; prev=arr_i
for idx,end in enumerate(aputs):
    start=None
    for k in range(prev+1,end+1):
        if re.match(r'\s*new-instance\s+',method[k]):
            start=k; break
    if start is None: raise SystemExit(f'no new-instance for module slot {idx}')
    blocks.append((idx,start,end)); prev=end
for idx,start,end in reversed(blocks):
    if idx in REMOVE:
        del method[start:end+1]
new_aputs=[i for i,l in enumerate(method) if i>arr_i and re.match(r'\s*aput-object\s+(\w+),\s+v11,\s+\w+',l)]
if len(new_aputs)!=kept_count: raise SystemExit(f'kept module count mismatch {len(new_aputs)} != {kept_count}')
offset=0
for newidx,pos0 in enumerate(new_aputs):
    pos=pos0+offset
    m=re.match(r'(\s*)aput-object\s+(\w+),\s+v11,\s+\w+',method[pos])
    indent,obj=m.group(1),m.group(2)
    method[pos:pos+1]=[f'{indent}const/16 v23, 0x{newidx:x}',f'{indent}aput-object {obj}, v11, v23']
    offset+=1
lines[mi:me+1]=method
eqt.write_text('\n'.join(lines)+'\n')

print(f'patched Meboard stage1; removed {len(REMOVE)} module roots; registry now {kept_count} entries')
