#!/usr/bin/env python3
"""Read compiled DEX indexes, APK payloads and replay equality for Stage 25.
This checks package structure and exact removed references, not ART execution.
"""
from __future__ import annotations
import argparse,hashlib,json,re,struct,zipfile,zlib
from pathlib import Path

REMOVED={'Ludo;','Ludn;','Ludh;'}
CTOR='(Laals;Laals;Laals;Laals;Laals;Laals;Laals;I[S)V'
MARKERS=('primes.packageMetric.lastSendTime',
'com/google/android/libraries/performance/primes/metrics/storage/PackageStatsCaptureO',
'com/google/android/libraries/performance/primes/metrics/storage/DirStatsCapture')

def require(ok,why):
    if not ok:raise ValueError(why)

def sig(n):return re.fullmatch(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))',n,re.I) is not None

def dex(data):
    require(data[:4]==b'dex\n','not dex')
    require(data[12:32]==hashlib.sha1(data[32:]).digest(),'DEX SHA-1 invalid')
    require(struct.unpack_from('<I',data,8)[0]==zlib.adler32(data[12:])&0xffffffff,'DEX checksum invalid')
    require(struct.unpack_from('<I',data,32)[0]==len(data),'DEX size invalid')
    def u32(off):return struct.unpack_from('<I',data,off)[0]
    strings=[]
    for i in range(u32(56)):
        off=u32(u32(60)+i*4)
        while data[off]&128:off+=1
        off+=1;end=data.index(b'\0',off)
        strings.append(data[off:end].decode('utf-8',errors='replace'))
    types=[strings[u32(u32(68)+i*4)] for i in range(u32(64))]
    protos=[]
    for i in range(u32(72)):
        _,ret,args=struct.unpack_from('<III',data,u32(76)+i*12)
        parts=[] if not args else [types[struct.unpack_from('<H',data,args+4+j*2)[0]] for j in range(u32(args))]
        protos.append('('+''.join(parts)+')'+types[ret])
    members=[]
    for i in range(u32(88)):
        cls,proto,name=struct.unpack_from('<HHI',data,u32(92)+i*8)
        members.append(types[cls]+'->'+strings[name]+protos[proto])
    defs={types[u32(u32(100)+i*32)] for i in range(u32(96))}
    return {'types':set(types),'members':set(members),'classes':defs}

def verify(before:Path,after:Path,replay:Path):
    with zipfile.ZipFile(before) as b,zipfile.ZipFile(after) as a,zipfile.ZipFile(replay) as r:
        for z in [b,a,r]:require(z.testzip() is None,'ZIP CRC failure')
        sets=[{n for n in z.namelist() if not sig(n)} for z in [b,a,r]]
        require(sets[0]==sets[1]==sets[2],'payload entry set changed')
        changed=sorted(n for n in sets[0] if b.read(n)!=a.read(n))
        require(changed==['classes.dex','classes3.dex'],'unexpected package delta')
        require(all(a.read(n)==r.read(n) for n in sets[0]),'clean replay differs')
        differences={};bdefs=set();adefs=set();old_ctor='Ltgh;-><init>'+CTOR
        before_ctor=False
        for name in sorted(n for n in sets[0] if re.fullmatch(r'classes\d*\.dex',n)):
            bd,ad=dex(b.read(name)),dex(a.read(name));bdefs|=bd['classes'];adefs|=ad['classes']
            require(not ad['types'].intersection(REMOVED),'deleted descriptor in type index')
            require(old_ctor not in ad['members'],'deleted constructor in method index')
            before_ctor |= old_ctor in bd['members']
            differences[name]={'classes_before':len(bd['classes']),'classes_after':len(ad['classes']),
                              'deleted':sorted(bd['classes']-ad['classes']),'added':sorted(ad['classes']-bd['classes'])}
        require(before_ctor,'before input did not contain removed constructor')
        require(bdefs-adefs==REMOVED and not adefs-bdefs,'class definition delta is not exact')
        marker_counts={}
        for marker in MARKERS:
            old=sum(b.read(n).count(marker.encode()) for n in sets[0]);new=sum(a.read(n).count(marker.encode()) for n in sets[0])
            require(old>0 and new==0,'marker check failed: '+marker)
            marker_counts[marker]={'before':old,'after':new}
        native=[n for n in sets[0] if n.startswith('lib/') and n.endswith('.so')]
        token_hits={}
        for token in ['udo','udn','udh','tgh','Ludo;','Ludn;','Ludh;','Ltgh;']:
            token_hits[token]=[n for n in native if b'\0'+token.encode()+b'\0' in b.read(n)]
        reviewed_false_positives=[]
        for token, libs in token_hits.items():
            for lib in libs:
                data=b.read(lib)
                # Reviewed exact accidental ASCII in the first int32 field of
                # a Tenor unwind-index pair, not an ELF string/JNI class name.
                require(token=='tgh' and lib=='lib/arm64-v8a/libtenoranimation_jni.so',
                        'unreviewed native name match')
                require(hashlib.sha256(data).hexdigest()=='ec3dd77ce6708b7544c3cfa7f9e23a9cd1048af5646d43faf71b5518f23efdc8', 'reviewed native input drift')
                needle=b'\0tgh\0';positions=[m.start() for m in re.finditer(re.escape(needle),data)]
                require(positions==[0x1efb83], 'native match location drift')
                require(data[:6]==b'\x7fELF\x02\x01','unexpected native ELF format')
                shoff=struct.unpack_from('<Q',data,40)[0]
                size,number,strings=struct.unpack_from('<HHH',data,58)
                sections=[struct.unpack_from('<IIQQQQIIQQ',data,shoff+i*size) for i in range(number)]
                names=sections[strings];names=data[names[4]:names[4]+names[5]]
                found=[x for x in sections if names[x[0]:].split(b'\0')[0]==b'.eh_frame_hdr']
                require(len(found)==1, 'unwind section not found')
                start=found[0][4];count=struct.unpack_from('<I',data,start+8)[0]
                require(data[start:start+4]==b'\x01\x1b\x03\x3b','unwind header encoding drift')
                actual=positions[0]+1;rel=actual-start-12
                require(rel>=0 and rel%8==0 and rel//8<count and actual+4<=start+found[0][5],
                        'match not an unwind-index field')
                reviewed_false_positives.append({'token':token,'library':lib,'file_offset':actual,
                    'section':'.eh_frame_hdr','table_entry':rel//8,
                    'classification':'first int32 field in an unwind index pair, not a string-table entry'})
        report={'passed':True,'input_sha256':hashlib.sha256(before.read_bytes()).hexdigest(),
                'apk_sha256':hashlib.sha256(after.read_bytes()).hexdigest(),'apk_size_bytes':after.stat().st_size,
                'unsigned_replay_sha256':hashlib.sha256(replay.read_bytes()).hexdigest(),
                'changed_entries':changed,'unchanged_entries':len(sets[0])-len(changed),'payload_entries':len(sets[0]),
                'dex_class_delta':differences,'class_count_before':len(bdefs),'class_count_after':len(adefs),
                'removed_types_absent':True,'removed_constructor_absent':True,'marker_counts':marker_counts,
                'native_library_count':len(native),'native_payloads_unchanged':all(a.read(n)==b.read(n) for n in native),
                'native_raw_token_hits':token_hits,'reviewed_native_false_positives':reviewed_false_positives,'all_replay_payloads_identical':True,
                'runtime_tested':False,'privacy_final':False}
        return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('replay',type=Path);p.add_argument('--json',type=Path)
    a=p.parse_args();out=json.dumps(verify(a.before,a.after,a.replay),indent=2)+'\n'
    if a.json:a.json.write_text(out)
    print(out)
if __name__=='__main__':main()
