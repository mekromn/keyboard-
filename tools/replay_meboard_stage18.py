#!/usr/bin/env python3
"""Replay the committed Meboard pipeline, then apply stage-18 Mozc excision."""
from __future__ import annotations
from pathlib import Path
import argparse,hashlib,subprocess,sys,zipfile

HERE=Path(__file__).resolve().parent
WORK=Path('/mnt/data/meboard_work')

def run(*args):
    print('+',' '.join(map(str,args)),flush=True)
    subprocess.run([str(x) for x in args],check=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--bundle',type=Path,default=Path('/mnt/data/Gboard_175940518_18.0.3.954559732-release-arm64-v8a.aspk'))
    ap.add_argument('--apktool',type=Path,default=Path('/mnt/data/meboard_tools/android/apktool/apktool.jar'))
    ap.add_argument('--aapt2',type=Path,default=Path('/mnt/data/meboard_tools/android/build-tools/aapt2'))
    a=ap.parse_args()
    run(sys.executable,HERE/'replay_meboard_pipeline.py','--bundle',a.bundle,'--apktool',a.apktool,'--aapt2',a.aapt2,'--no-checkpoints')
    run(sys.executable,HERE/'remove_mozc_telemetry_complete.py')
    out=WORK/'checkpoints/Meboard-stage18-mozc-unsigned.apk';out.parent.mkdir(parents=True,exist_ok=True)
    run('java','-jar',a.apktool,'b','--aapt',a.aapt2,'-f','-j','4','-o',out,WORK/'buildtree')
    with zipfile.ZipFile(out) as z:
        bad=z.testzip();dex=sorted(n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex'))
        if bad:raise SystemExit(f'corrupt ZIP member {bad}')
        if len(dex)!=4:raise SystemExit(f'expected four DEX files, got {dex}')
    h=hashlib.sha256(out.read_bytes()).hexdigest()
    print(f'STAGE18 OK: {out} size={out.stat().st_size} sha256={h} dex={dex}')
if __name__=='__main__':main()
