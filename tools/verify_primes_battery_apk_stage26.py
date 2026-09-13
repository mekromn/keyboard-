#!/usr/bin/env python3
"""Compiled APK/type/reference/layout comparison for the exact Stage-26 removal."""
from pathlib import Path
import argparse,hashlib,json,re,struct,zipfile,zlib
REMOVED={'Ltys;','Ltyr;','Ltyq;','Ltzb;'}
MARKERS=('primes.battery.snapshot','com/google/android/libraries/performance/primes/metrics/battery/BatteryMetricServiceImpl')
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
    raw=after.read_bytes()
    with zipfile.ZipFile(before) as b,zipfile.ZipFile(after) as a,zipfile.ZipFile(replay) as r:
        for z in [b,a,r]:
            require(z.testzip() is None,'ZIP CRC failure')
            require(len(z.namelist())==len(set(z.namelist())),'Duplicate ZIP name')
        names={n for n in b.namelist() if not sig(n)}
        require(names=={n for n in a.namelist() if not sig(n)}=={n for n in r.namelist() if not sig(n)},'Entry set drift')
        changed=[];replay_diff=[];native=[];dex_delta={};bdefs=set();adefs=set();bstored=0;astored=0
        marker_counts={m:{'before':0,'after':0} for m in MARKERS}
        for name in sorted(names):
            old,new=b.read(name),a.read(name)
            if old!=new:changed.append(name)
            if new!=r.read(name):replay_diff.append(name)
            bi,ai=b.getinfo(name),a.getinfo(name)
            require(bi.compress_type==ai.compress_type,'Compression mode changed')
            for m in MARKERS:
                marker_counts[m]['before']+=old.count(m.encode());marker_counts[m]['after']+=new.count(m.encode())
            if re.fullmatch(r'classes\d*\.dex',name):
                bd,ad=dex(old),dex(new);bdefs|=bd['classes'];adefs|=ad['classes'];bstored+=len(old);astored+=len(new)
                require(not ad['types'].intersection(REMOVED),'Deleted type reference remains')
                dex_delta[name]={'bytes_before':len(old),'bytes_after':len(new),'deleted':sorted(bd['classes']-ad['classes']),'added':sorted(ad['classes']-bd['classes'])}
            h=struct.unpack_from('<IHHHHHIIIHH',raw,ai.header_offset);data_offset=ai.header_offset+30+h[-2]+h[-1]
            if ai.compress_type==0:require(data_offset%(16384 if name.endswith('.so') else 4)==0,'Bad data alignment: '+name)
            if name.startswith('lib/') and name.endswith('.so'):
                require(old==new,'Native payload changed');native.append((name,new))
        require(changed==['classes.dex','classes3.dex'],'Unexpected payload changes')
        require(not replay_diff,'Independent replay differs')
        require(bdefs-adefs==REMOVED and not adefs-bdefs,'Unexpected compiled class change')
        require(all(v['before']>0 and v['after']==0 for v in marker_counts.values()),'Marker check failed')
        # Short ASCII "tyr" is an ICU locale-table entry in two libraries, not
        # a unique JVM descriptor. Guard every exact hit and the adjacent table.
        reviewed=[]
        allowed={
          'lib/arm64-v8a/libintegrated_shared_object.so':('1dce4b3d9424d63c6fd6917fedb8b3c7fca37db8bde43c82dc4ed1120114a836',4971498),
          'lib/arm64-v8a/libdictation_jni.so':('5a0a7cea229de98fedb0cb167875b692ab62f1153f1ff31d104dceff7f78cf0f',763918)}
        context=b'\x00twm\x00txg\x00txo\x00tyr\x00tyv\x00ude\x00udg\x00udi\x00udm\x00ug\x00ug_KZ\x00ug_MN\x00'
        for token in ['tys','tyr','tyq','tzb','Ltys;','Ltyr;','Ltyq;','Ltzb;']:
            for name,d in native:
                hits=[m.start() for m in re.finditer(re.escape(b'\0'+token.encode()+b'\0'),d)]
                if not hits:continue
                require(token=='tyr' and name in allowed,'Unreviewed native name match')
                sha,pos=allowed[name];require(hashlib.sha256(d).hexdigest()==sha and hits==[pos],'Native match drift')
                start=pos-context.index(b'\0tyr\0');require(d[start:start+len(context)]==context,'Locale-table sequence changed')
                shoff=struct.unpack_from('<Q',d,40)[0];entsz,num,ss=struct.unpack_from('<HHH',d,58)
                sections=[struct.unpack_from('<IIQQQQIIQQ',d,shoff+i*entsz) for i in range(num)];st=sections[ss];ns=d[st[4]:st[4]+st[5]]
                require(any(ns[s[0]:].split(b'\0')[0]==b'.rodata' and s[4]<=pos<s[4]+s[5] for s in sections),'Expected .rodata match')
                reviewed.append({'token':token,'library':name,'offset':pos,'classification':'ICU locale-to-script table sequence; no native bytes changed'})
        require(len(reviewed)==2,'Expected native match accounting changed')
        return {'passed':True,'input_sha256':hashlib.sha256(before.read_bytes()).hexdigest(),'apk_sha256':hashlib.sha256(raw).hexdigest(),
         'apk_bytes':len(raw),'input_apk_bytes':before.stat().st_size,'apk_bytes_saved':before.stat().st_size-len(raw),
         'dex_bytes_before':bstored,'dex_bytes_after':astored,'dex_bytes_saved':bstored-astored,
         'classes_before':len(bdefs),'classes_after':len(adefs),'dex_class_delta':dex_delta,'marker_counts':marker_counts,
         'payload_entries':len(names),'changed_entries':changed,'unchanged_entries':len(names)-len(changed),
         'unchanged_native_libraries':len(native),'compression_modes_unchanged':True,'alignment_16k_native_4_other':True,
         'all_replay_payloads_identical':True,'unsigned_replay_sha256':hashlib.sha256(replay.read_bytes()).hexdigest(),
         'reviewed_native_name_matches':reviewed,'runtime_tested':False,'privacy_final':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('replay',type=Path);p.add_argument('--json',type=Path);a=p.parse_args();s=json.dumps(verify(a.before,a.after,a.replay),indent=2)+'\n'
    if a.json:a.json.write_text(s)
    print(s)
if __name__=='__main__':main()
