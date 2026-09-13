#!/usr/bin/env python3
"""Read-only byte accounting: real code/payload savings versus ZIP alignment."""
from pathlib import Path
import argparse,hashlib,json,struct,zipfile

def audit(p:Path):
    data=p.read_bytes();entries=[]
    with zipfile.ZipFile(p) as z:
        for i in z.infolist():
            h=struct.unpack_from('<IHHHHHIIIHH',data,i.header_offset)
            if h[0]!=0x04034b50:raise ValueError('Invalid local header')
            fn,ex=h[-2:];offset=i.header_offset+30+fn+ex
            entries.append(dict(name=i.filename,uncompressed=i.file_size,packed=i.compress_size,method=i.compress_type,
                offset=offset,local_header=i.header_offset,local_extra=ex,central_extra=len(i.extra)))
        packed=sum(i['packed'] for i in entries)
        local=sum(30+len(i.filename.encode())+n['local_extra'] for i,n in zip(z.infolist(),entries))
        central=sum(46+len(i.filename.encode())+len(i.extra)+len(i.comment) for i in z.infolist())
        end=max(i['offset']+i['packed'] for i in entries)
        result=dict(file=p.name,sha256=hashlib.sha256(data).hexdigest(),apk_bytes=len(data),packed_payload_bytes=packed,
           dex_bytes=sum(i['uncompressed'] for i in entries if i['name'].endswith('.dex')),
           native_bytes=sum(i['uncompressed'] for i in entries if i['name'].endswith('.so')),
           local_extra_bytes=sum(i['local_extra'] for i in entries),local_header_bytes=local,central_directory_bytes=central,
           gap_to_central_directory=z.start_dir-end,end_record_bytes=len(data)-z.start_dir-central,entries=entries)
        if len(data)!=packed+local+central+result['gap_to_central_directory']+result['end_record_bytes']:
            raise ValueError('Byte accounting did not close')
        return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('apks',type=Path,nargs='+');p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    results=[audit(f) for f in a.apks];a.json.write_text(json.dumps(results,indent=2)+'\n')
    for r in results:print(json.dumps({k:v for k,v in r.items() if k!='entries'},indent=2))
if __name__=='__main__':main()
