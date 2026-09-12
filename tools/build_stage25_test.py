#!/usr/bin/env python3
"""Rebuild a Stage-25 TEST from the exact verified Stage-24 APK.

A new empty work directory is required. No credentials or APKs belong in GitHub.
Unsigned output is the default; pass --build-tools, --keystore, --alias and
--password-env together to align/sign with the existing private Meboard key.
This script never promotes a candidate to the working baseline.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, os, re, shutil, struct, subprocess, sys, zipfile, zlib
from pathlib import Path
from remove_primes_storage_stage25 import apply
from verify_primes_storage_stage25 import verify

INPUT_SHA='d7c77f87c45eca6a91f7c5bdfcc0667f287c87f09c57890563609a5376bb5d46'
TOOL_SHA='dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423'
SIGNER_SHA='23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15'
HERE=Path(__file__).resolve().parent


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def signature(name):return bool(re.match(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))$',name,re.I))
def require(condition,message):
    if not condition:raise RuntimeError(message)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path);p.add_argument('--apktool',required=True,type=Path)
    p.add_argument('--work',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--build-tools',type=Path);p.add_argument('--keystore',type=Path)
    p.add_argument('--alias');p.add_argument('--password-env')
    args=p.parse_args()
    for k in ('input','apktool','work','output','build_tools','keystore'):
        if getattr(args,k,None) is not None:setattr(args,k,getattr(args,k).resolve())
    require(digest(args.input)==INPUT_SHA,'Input APK is not the reviewed Stage-24 checkpoint')
    require(digest(args.apktool)==TOOL_SHA,'Require the pinned Apktool 3.0.3 binary')
    require(not args.output.exists(),'Output already exists; refuse overwrite')
    require(not args.work.exists() or not any(args.work.iterdir()),'Use an empty work directory')
    signing=[args.build_tools,args.keystore,args.alias,args.password_env]
    require(not any(signing) or all(signing),'Provide all four signing options together')
    if args.password_env:require(args.password_env in os.environ,'Password environment variable is unset')
    work=args.work;work.mkdir(parents=True,exist_ok=True)
    reports=work/'reports';reports.mkdir()
    env=os.environ.copy()
    if args.build_tools:env['LD_LIBRARY_PATH']=str(args.build_tools/'lib64')+os.pathsep+env.get('LD_LIBRARY_PATH','')
    def run(command,log):
        with (reports/log).open('w') as f:
            result=subprocess.run([str(x) for x in command],stdout=f,stderr=subprocess.STDOUT,env=env)
        require(result.returncode==0,f'{log} failed; see local report')
    baseline=work/'baseline';patched=work/'patched';compiler=work/'compiler';compiler.mkdir()
    run(['java','-Xmx2g','-jar',args.apktool,'d','-f','-j','4','-o',baseline,args.input],'decode.log')
    shutil.copytree(baseline,patched)
    apply(patched,reports/'removal.json')
    preservation=verify(baseline,patched)
    (reports/'preservation.json').write_text(json.dumps(preservation,indent=2)+'\n')
    run(['javac','-cp',args.apktool,'-d',compiler,HERE/'MeboardSmaliAssembler.java'],'javac.log')
    dexes={}
    for directory,name in [('smali','classes.dex'),('smali_classes3','classes3.dex')]:
        output=work/name
        run(['java','-Xmx2g','-cp',str(args.apktool)+os.pathsep+str(compiler),
             'MeboardSmaliAssembler',patched/directory,output,'32'],name+'.log')
        data=output.read_bytes()
        require(data[:4]==b'dex\n' and struct.unpack_from('<I',data,32)[0]==len(data),'DEX header invalid')
        require(data[12:32]==hashlib.sha1(data[32:]).digest(),'DEX SHA-1 invalid')
        require(struct.unpack_from('<I',data,8)[0]==zlib.adler32(data[12:])&0xffffffff,'DEX checksum invalid')
        dexes[name]=data
    unsigned=work/'stage25-unsigned.apk'
    with zipfile.ZipFile(args.input) as source,zipfile.ZipFile(unsigned,'w') as target:
        require(len(set(source.namelist()))==len(source.namelist()),'Duplicate ZIP entry')
        for info in source.infolist():
            if signature(info.filename):continue
            data=dexes.get(info.filename)
            if data is None:data=source.read(info.filename)
            info=copy.copy(info);info.extra=b''
            target.writestr(info,data)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    certificate=None
    if args.keystore:
        aligned=work/'stage25-aligned.apk'
        run([args.build_tools/'zipalign','-P','16','-f','4',unsigned,aligned],'align.log')
        signer=args.build_tools/'lib/apksigner.jar'
        run(['java','-jar',signer,'sign','--ks',args.keystore,'--ks-type','PKCS12',
             '--ks-key-alias',args.alias,'--ks-pass','env:'+args.password_env,
             '--v1-signing-enabled','false','--v2-signing-enabled','true',
             '--v3-signing-enabled','true','--v4-signing-enabled','false',
             '--out',args.output,aligned],'sign.log')
        run(['java','-jar',signer,'verify','--verbose','--print-certs',args.output],'verify-signature.log')
        s=(reports/'verify-signature.log').read_text()
        m=re.search(r'certificate SHA-256 digest: (\w+)',s)
        require(m is not None and m[1]==SIGNER_SHA,'Signing certificate mismatch')
        require('Verified using v3 scheme (APK Signature Scheme v3): true' in s,'V3 verification failed')
        certificate=m[1]
        run([args.build_tools/'zipalign','-c','-P','16','-v','4',args.output],'verify-alignment.log')
    else:shutil.copyfile(unsigned,args.output)
    with zipfile.ZipFile(args.input) as before,zipfile.ZipFile(args.output) as after:
        require(after.testzip() is None,'ZIP CRC failure')
        bn={n for n in before.namelist() if not signature(n)}
        an={n for n in after.namelist() if not signature(n)}
        require(bn==an,'Payload entry set changed')
        changed=sorted(n for n in bn if before.read(n)!=after.read(n))
        require(changed==['classes.dex','classes3.dex'],'Unexpected non-code payload delta')
    state={'input_sha256':INPUT_SHA,'output_sha256':digest(args.output),'output_file':args.output.name,
           'changed_payload_entries':changed,'payload_entry_count':len(an),
           'signer_certificate_sha256':certificate,'signed':bool(certificate),
           'runtime_tested':False,'privacy_final':False,'preservation':preservation,
           'dex_sha256':{n:hashlib.sha256(b).hexdigest() for n,b in dexes.items()}}
    (reports/'build-state.json').write_text(json.dumps(state,indent=2)+'\n')
    print(json.dumps(state,indent=2))


if __name__=='__main__':main()
