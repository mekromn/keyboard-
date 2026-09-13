#!/usr/bin/env python3
"""Measure actual APK payload, local-header padding, overhead and alignment.
This reads local headers: central-directory extras alone miss zipalign padding.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,re,struct,zipfile
from pathlib import Path

def audit(path:Path)->dict:
    raw=path.read_bytes();items=[];cats=collections.Counter();payload=0;uncompressed=0;extra=0;headers=0;end=0
    with zipfile.ZipFile(path) as z:
        bad=z.testzip()
        if bad:raise ValueError('CRC failure: '+bad)
        for i in z.infolist():
            off=i.header_offset
            if raw[off:off+4]!=b'PK\x03\x04':raise ValueError('Bad local header')
            nl,el=struct.unpack_from('<HH',raw,off+26);start=off+30+nl+el
            if i.flag_bits&8:raise ValueError('Data descriptor accounting is not enabled')
            need=16384 if i.filename.endswith('.so') and i.compress_type==0 else 4 if i.compress_type==0 else 1
            if start%need:raise ValueError('Alignment failed: '+i.filename)
            end=max(end,start+i.compress_size);payload+=i.compress_size;uncompressed+=i.file_size;extra+=el;headers+=30+nl
            cat='native' if i.filename.endswith('.so') else 'dex' if re.fullmatch(r'classes\d*\.dex',i.filename) else 'assets' if i.filename.startswith('assets/') else 'resources' if i.filename.startswith('res/') or i.filename=='resources.arsc' else 'other'
            cats[cat]+=i.compress_size
            items.append({'name':i.filename,'payload_bytes':i.compress_size,'uncompressed_bytes':i.file_size,'local_extra_bytes':el,'data_offset':start,'compression_method':i.compress_type})
        central=len(raw)-z.start_dir;gap=z.start_dir-end
        if payload+extra+headers+gap+central!=len(raw):raise ValueError('Layout accounting mismatch')
    return {'file':path.name,'sha256':hashlib.sha256(raw).hexdigest(),'apk_bytes':len(raw),
      'stored_payload_bytes':payload,'uncompressed_payload_bytes':uncompressed,'payload_categories':dict(cats),
      'local_extra_bytes':extra,'local_headers_without_extras':headers,'signing_block_and_gap_bytes':gap,
      'central_directory_and_end_bytes':central,'sum_verified':True,'native_16k_alignment':True,
      'stored_entry_4byte_alignment':True,'entries':items}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('apks',nargs='+',type=Path);p.add_argument('--json',type=Path)
    a=p.parse_args();s=json.dumps([audit(x) for x in a.apks],indent=2)+'\n'
    if a.json:a.json.write_text(s)
    print(s)
if __name__=='__main__':main()
