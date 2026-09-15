#!/usr/bin/env python3
"""Create Stage 43 unsigned hybrid payload from pinned Stage 42 + Stage 29 APKs.

This intentionally copies only the resource-safe Stage-28 privacy cleanup payloads
from Stage 29. It does not copy Stage 29 main DEX, manifest, theme or microphone code.
Run zipalign and sign separately with the private stable Meboard key.
"""
from pathlib import Path
import hashlib, zipfile, argparse

ST42_SHA='522e1950349cd1a65f829a8d5a03d06d84d23a8f9e2bc551b97b9b9197b0cbb5'
ST29_SHA='8da8eb3b7e886c8e5c4d2d7ed467780e2b85d7fdb47590ccf713727ae17d1152'
REPLACE={
    'classes2.dex',
    'res/xml/setting_privacy.xml',
    'res/xml/APKTOOL_RENAMED_0x7f170002.xml',
}

def sha256(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--stage42', type=Path, required=True)
    ap.add_argument('--stage29', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a=ap.parse_args()
    if sha256(a.stage42)!=ST42_SHA: raise SystemExit('Stage42 hash mismatch')
    if sha256(a.stage29)!=ST29_SHA: raise SystemExit('Stage29 hash mismatch')
    with zipfile.ZipFile(a.stage42) as zs, zipfile.ZipFile(a.stage29) as zd, zipfile.ZipFile(a.output,'w',allowZip64=True) as zo:
        if zs.namelist()!=list(dict.fromkeys(zs.namelist())): raise SystemExit('duplicate Stage42 entries')
        for name in zs.namelist():
            old=zs.getinfo(name)
            data=(zd if name in REPLACE else zs).read(name)
            zi=zipfile.ZipInfo(old.filename, old.date_time)
            zi.compress_type=old.compress_type
            zi.comment=old.comment; zi.extra=old.extra
            zi.internal_attr=old.internal_attr; zi.external_attr=old.external_attr
            zi.create_system=old.create_system; zi.create_version=old.create_version
            zi.extract_version=old.extract_version; zi.flag_bits=old.flag_bits & ~0x08
            zo.writestr(zi,data,compress_type=old.compress_type,compresslevel=9 if old.compress_type==zipfile.ZIP_DEFLATED else None)

if __name__=='__main__': main()
