#!/usr/bin/env python3
"""Verify compiled removal, original payload preservation, native token context,
and same-stage replay equality. Does not execute ART or certify network silence.
"""
from __future__ import annotations
import argparse,hashlib,json,re,struct,zipfile,zlib
from pathlib import Path
REMOVED={'Ludx;', 'Luad;', 'Luai;', 'Luag;', 'Lued;', 'Luec;', 'Luae;', 'Luaf;', 'Luaq;'}
MARKERS=('primes/crash','com/google/android/libraries/performance/primes/metrics/crash/CrashMetricFactory','CrashMetricFactory.java')
def require(ok,why):
    if not ok:raise ValueError(why)

def sig(n):return re.fullmatch(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))',n,re.I) is not None

def dex(data):
    require(data[:4]==b'dex\n','not dex')
    require(data[12:32]==hashlib.sha1(data[32:]).digest(),'DEX SHA-1 invalid')
    require(struct.unpack_from('<I',data,8)[0]==zlib.adler32(data[12:])&0xffffffff,'DEX checksum invalid')
    require(struct.unpack_from('<I',data,32)[0]==len(data),'DEX size invalid')
    def u32(o):return struct.unpack_from('<I',data,o)[0]
    strings=[]
    for i in range(u32(56)):
        off=u32(u32(60)+i*4)
        while data[off]&128:off+=1
        off+=1;end=data.index(b'\0',off)
        strings.append(data[off:end].decode('utf-8',errors='replace'))
    types=[strings[u32(u32(68)+i*4)] for i in range(u32(64))]
    defs={types[u32(u32(100)+i*32)] for i in range(u32(96))}
    return {'types':set(types),'classes':defs,'strings':set(strings)}

def section_at(data,pos):
    require(data[:6]==b'\x7fELF\x02\x01','unexpected ELF')
    off=struct.unpack_from('<Q',data,40)[0]
    size,count,index=struct.unpack_from('<HHH',data,58)
    secs=[struct.unpack_from('<IIQQQQIIQQ',data,off+i*size) for i in range(count)]
    n=secs[index];names=data[n[4]:n[4]+n[5]]
    return [names[s[0]:].split(b'\0')[0].decode() for s in secs if s[4]<=pos<s[4]+s[5] and s[1]!=8]

def native_review(z):
    hits=[]
    for name in z.namelist():
        if not name.startswith('lib/') or not name.endswith('.so'):continue
        data=z.read(name)
        for token in sorted(REMOVED|{d[1:-1] for d in REMOVED}):
            needle=token.encode()+b'\0'; pos=0
            while True:
                off=data.find(needle,pos)
                if off<0:break
                if off==0 or data[off-1]==0:hits.append({'file':name,'token':token,'offset':off})
                pos=off+len(needle)
    require(not hits,'Unreviewed exact native class-name token: '+repr(hits))
    return hits

def verify(before:Path,after:Path,replay:Path):
    with zipfile.ZipFile(before) as b,zipfile.ZipFile(after) as a,zipfile.ZipFile(replay) as r:
        for z in (b,a,r):
            require(len(z.namelist())==len(set(z.namelist())),'Duplicate ZIP member')
            require(z.testzip() is None,'ZIP CRC failure')
        sets=[{n for n in z.namelist() if not sig(n)} for z in (b,a,r)]
        require(sets[0]==sets[1]==sets[2],'APK payload entry set changed')
        changed=sorted(n for n in sets[0] if b.read(n)!=a.read(n))
        require(changed==['classes.dex'],'Unexpected changed APK entries')
        require(all(a.read(n)==r.read(n) for n in sets[0]),'Clean replay payload differs')
        bd=set();ad=set();details={};before_dex=0;after_dex=0
        for n in sorted(x for x in sets[0] if re.fullmatch(r'classes\d*\.dex',x)):
            x,y=b.read(n),a.read(n);before_dex+=len(x);after_dex+=len(y)
            dx,dy=dex(x),dex(y);bd|=dx['classes'];ad|=dy['classes']
            require(not dy['types']&REMOVED,'Deleted type reference retained in compiled DEX')
            details[n]={'bytes_before':len(x),'bytes_after':len(y),'classes_deleted':sorted(dx['classes']-dy['classes']),'classes_added':sorted(dy['classes']-dx['classes'])}
        require(bd-ad==REMOVED and not ad-bd,'Unexpected compiled class definition delta')
        marks={}
        for m in MARKERS:
            old=sum(b.read(n).count(m.encode()) for n in sets[0]);new=sum(a.read(n).count(m.encode()) for n in sets[0])
            require(old>0 and new==0,'Reporter marker check failed')
            marks[m]={'before':old,'after':new}
        native=native_review(a)
        natives=[n for n in sets[0] if n.startswith('lib/') and n.endswith('.so')]
        require(all(b.read(n)==a.read(n) for n in natives),'Native library changed')
        return {'passed':True,'input_sha256':hashlib.sha256(before.read_bytes()).hexdigest(),
          'apk_sha256':hashlib.sha256(after.read_bytes()).hexdigest(),'apk_size_bytes':after.stat().st_size,
          'unsigned_replay_sha256':hashlib.sha256(replay.read_bytes()).hexdigest(),
          'class_count_before':len(bd),'class_count_after':len(ad),'compiled_dex_bytes_removed':before_dex-after_dex,
          'dex_details':details,'changed_entries':changed,'payload_entries':len(sets[0]),
          'unchanged_entries':len(sets[0])-len(changed),'all_replay_payloads_identical':True,
          'marker_counts':marks,'native_library_count':len(natives),'native_payloads_unchanged':True,
          'native_exact_name_hits':native,'runtime_tested':False,'privacy_final':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('replay',type=Path);p.add_argument('--json',type=Path)
    x=p.parse_args();s=json.dumps(verify(x.before,x.after,x.replay),indent=2)+'\n'
    if x.json:x.json.write_text(s)
    print(s)
if __name__=='__main__':main()
