#!/usr/bin/env python3
"""Build an aligned unsigned Stage-27 test from the exact Stage-26 input.
Preserves original compression methods, aligns stored native libraries to 16 KiB,
and checks all surviving source files. Sign the output separately for device use.
This driver does not publish or promote builds, or handle signing credentials.
"""
from __future__ import annotations
import argparse,copy,hashlib,io,json,os,re,subprocess,sys,zipfile
from pathlib import Path
from remove_primes_crash_support_stage27 import apply
from verify_primes_crash_support_stage27 import verify
from verify_primes_crash_support_apk_stage27 import dex
from apk_layout_audit import audit
INPUT_SHA='acd77999d2654af314fbb4fc7b248f986084471564b2a0185dffd26d2d621dd8'
# Actual recovered Apktool 3.0.3 used in this stage, measured from its bytes.
TOOL_SHA='dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423'
HERE=Path(__file__).resolve().parent

def require(ok,message):
    if not ok:raise RuntimeError(message)

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def signature(n):return re.fullmatch(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))',n,re.I) is not None

def buffered_copy_tree(source:Path,target:Path):
    # Do not use sendfile/reflink copies. Every byte is explicitly read/written,
    # then verified again from the destination.
    target.mkdir(parents=True)
    for p in source.rglob('*'):
        rel=p.relative_to(source);q=target/rel
        if p.is_dir():q.mkdir(exist_ok=True)
        elif p.is_file():
            q.parent.mkdir(parents=True,exist_ok=True);data=p.read_bytes();q.write_bytes(data)
            require(q.read_bytes()==data,'Copy verification failed: '+str(rel))

def package(source:Path,output:Path,dexes:dict[str,bytes]):
    stream=io.BytesIO()
    with zipfile.ZipFile(source) as old,zipfile.ZipFile(stream,'w') as new:
        require(old.testzip() is None,'Input CRC failure')
        require(len(old.namelist())==len(set(old.namelist())),'Duplicate input entry')
        for original in old.infolist():
            if signature(original.filename):continue
            data=dexes.get(original.filename)
            if data is None:data=old.read(original.filename)
            info=copy.copy(original);info.extra=b''
            alignment=16384 if info.filename.endswith('.so') and info.compress_type==0 else 4 if info.compress_type==0 else 1
            # All entries of the pinned base have ASCII names; reject drift.
            name=info.filename.encode('ascii')
            padding=(-(stream.tell()+30+len(name)))%alignment
            info.extra=b'\0'*padding
            new.writestr(info,data)
            # Match zipalign's local-only padding; central directory needs none.
            info.extra=b''
    output.write_bytes(stream.getvalue())
    with zipfile.ZipFile(output) as z:require(z.testzip() is None,'Packaged CRC failure')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path);p.add_argument('--apktool',required=True,type=Path)
    p.add_argument('--work',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    for key in ('input','apktool','work','output'):
        if getattr(a,key) is not None:setattr(a,key,getattr(a,key).resolve())
    require(digest(a.input)==INPUT_SHA,'Require the exact Stage-26 APK')
    require(digest(a.apktool)==TOOL_SHA,'Apktool binary hash differs from the tested recovered binary')
    require(not a.output.exists(),'Refusing to overwrite output')
    require(not a.work.exists() or not any(a.work.iterdir()),'Use a new empty work directory')
    a.work.mkdir(parents=True,exist_ok=True);reports=a.work/'reports';reports.mkdir()
    def run(cmd,name):
        with (reports/name).open('w') as f:
            result=subprocess.run([str(x) for x in cmd],stdout=f,stderr=subprocess.STDOUT)
        require(result.returncode==0,'Command failed: '+name)
    baseline=a.work/'baseline';patched=a.work/'patched';compiler=a.work/'compiler';compiler.mkdir()
    run(['java','-Xmx2g','-jar',a.apktool,'d','-f','-j','4','-o',baseline,a.input],'decode.log')
    buffered_copy_tree(baseline,patched)
    removal=apply(patched,reports/'removal.json')
    preservation=verify(baseline,patched)
    (reports/'preservation.json').write_text(json.dumps(preservation,indent=2)+'\n')
    run(['javac','-cp',a.apktool,'-d',compiler,HERE/'MeboardSmaliAssembler.java'],'javac.log')
    dexes={}
    for directory,name in [('smali','classes.dex')]:
        output=a.work/name
        run(['java','-Xmx2g','-cp',str(a.apktool)+os.pathsep+str(compiler),'MeboardSmaliAssembler',patched/directory,output,'32'],name+'.log')
        data=output.read_bytes();dex(data);dexes[name]=data
    # Check again after assembly, not only immediately following the copy.
    require(verify(baseline,patched)==preservation,'Preservation changed after assembly')
    unsigned=a.work/'stage27-aligned-unsigned.apk';package(a.input,unsigned,dexes)
    audit(unsigned)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(unsigned.read_bytes())
    layout=audit(a.output)
    with zipfile.ZipFile(a.input) as b,zipfile.ZipFile(a.output) as z:
        bn={n for n in b.namelist() if not signature(n)};zn={n for n in z.namelist() if not signature(n)}
        require(bn==zn,'Payload entry set differs')
        changes=sorted(n for n in bn if b.read(n)!=z.read(n))
        require(changes==['classes.dex'],'Unexpected payload edit')
    state={'input_sha256':INPUT_SHA,'apk_sha256':digest(a.output),'apk_bytes':a.output.stat().st_size,
      'apktool_sha256':TOOL_SHA,'signed':False,
      'payload_entries':len(zn),'changed_entries':changes,'preservation':preservation,
      'compiled_dex_hashes':{n:hashlib.sha256(b).hexdigest() for n,b in dexes.items()},'runtime_tested':False,'privacy_final':False}
    (reports/'layout.json').write_text(json.dumps(layout,indent=2)+'\n')
    (reports/'build-state.json').write_text(json.dumps(state,indent=2)+'\n')
    print(json.dumps(state,indent=2))
if __name__=='__main__':main()
