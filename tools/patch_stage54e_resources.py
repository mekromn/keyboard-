#!/usr/bin/env python3
from pathlib import Path
import struct,sys,hashlib
if len(sys.argv)!=3:
    raise SystemExit('usage: patch_stage54e_resources.py <stage54d-resources.arsc> <out-resources.arsc>')
src=Path(sys.argv[1]); out=Path(sys.argv[2]); data=bytearray(src.read_bytes())
EXPECTED_SHA='c2d0c0e3ea65ea61c83b801a158da27b993da20af668c61baefc9914b198cb6b'
got=hashlib.sha256(data).hexdigest()
if got!=EXPECTED_SHA: raise SystemExit(f'input drift: {got} != {EXPECTED_SHA}')
repls={0x7f040195:0x7f0805a5,0x7f0401a1:0x7f0805eb,0x7f0401a3:0x7f0805f4,0x7f0401a4:0x7f0805f6,0x7f0401b0:0x7f0805fb,0x7f0401b1:0x7f0805fc,0x7f0401b2:0x7f0805fd,0x7f0401b5:0x7f080600,0x7f0401bc:0x7f08056e,0x7f0401bd:0x7f08056f}
for attr,draw in repls.items():
    pat=struct.pack('<I HBB I',attr,8,0,1,0)
    hits=[]; pos=0
    while True:
        i=data.find(pat,pos)
        if i<0: break
        hits.append(i); pos=i+1
    if len(hits)!=1: raise SystemExit(f'{attr:#x}: expected exactly one null bag entry, got {hits}')
    struct.pack_into('<I',data,hits[0]+8,draw)
out.write_bytes(data)
print('patched',len(repls),'exact stock keyboard-theme references')
print('sha256',hashlib.sha256(data).hexdigest())
