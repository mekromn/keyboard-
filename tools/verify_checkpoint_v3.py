#!/usr/bin/env python3
"""Independent, narrow APK-v3 RSA/SHA-512 content verification for this checkpoint.
Requires cryptography. Does not replace ART/device tests or support arbitrary
rotated/multi-signer APKs. v2 blocks are not verified by this tool.
"""
from pathlib import Path
import struct,hashlib,zipfile,json
if not __debug__: raise RuntimeError("Run without -O; verification assertions must remain enabled")
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import padding
class R:
 def __init__(self,d):self.d=d;self.o=0
 def u32(self):v=struct.unpack_from('<I',self.d,self.o)[0];self.o+=4;return v
 def lp(self):n=self.u32();v=self.d[self.o:self.o+n];assert len(v)==n;self.o+=n;return v
 def done(self):assert self.o==len(self.d),(self.o,len(self.d))
def seq(d):
 r=R(d);out=[]
 while r.o<len(d):out.append(r.lp())
 return out

def verify(path):
 d=path if isinstance(path,bytes) else Path(path).read_bytes();end=d.rfind(b'PK\x05\x06');assert end>=0
 cd=struct.unpack_from('<I',d,end+16)[0];csz=struct.unpack_from('<I',d,end+12)[0];assert cd+csz==end
 assert end+22+struct.unpack_from('<H',d,end+20)[0]==len(d)
 assert d[cd-16:cd]==b'APK Sig Block 42'
 sz=struct.unpack_from('<Q',d,cd-24)[0];start=cd-sz-8;assert struct.unpack_from('<Q',d,start)[0]==sz
 p=start+8;blocks={}
 while p<cd-24:
  n,ident=struct.unpack_from('<QI',d,p);blocks[ident]=d[p+12:p+8+n];p+=8+n
 assert p==cd-24
 eo=bytearray(d[end:]);struct.pack_into('<I',eo,16,start)
 pieces=[]
 for section in [memoryview(d)[:start],memoryview(d)[cd:end],memoryview(eo)]:
  for off in range(0,len(section),1048576):
   c=section[off:off+1048576];pieces.append(hashlib.sha512(b'\xa5'+struct.pack('<I',len(c))+c).digest())
 digest=hashlib.sha512(b'\x5a'+struct.pack('<I',len(pieces))+b''.join(pieces)).digest()
 result={'apk_sha256':hashlib.sha256(d).hexdigest(),'schemes':{}}
 for version,ident in [(3,0xf05368c0)]:
  v=R(blocks[ident]);ss=seq(v.lp());v.done();assert len(ss)==1
  r=R(ss[0]);signed=r.lp()
  sdk=(r.u32(),r.u32()) if version==3 else None
  sigs=seq(r.lp());pub=r.lp();r.done()
  sd=R(signed);ds=seq(sd.lp());certs=seq(sd.lp())
  inner=(sd.u32(),sd.u32()) if version==3 else None
  attrs=seq(sd.lp());sd.done();assert inner==sdk;assert not attrs;assert sdk[0]<=36<=sdk[1]
  parsed=[]
  for entry in sigs:
   it=R(entry);algo=it.u32();signature=it.lp();it.done();parsed.append((algo,signature))
  digs=[]
  for entry in ds:
   it=R(entry);algo=it.u32();value=it.lp();it.done();digs.append((algo,value))
  assert [a for a,_ in parsed]==[a for a,_ in digs]
  assert len(parsed)==1 and parsed[0][0]==0x104,(version,[hex(a) for a,_ in parsed])
  key=serialization.load_der_public_key(pub);key.verify(parsed[0][1],signed,padding.PKCS1v15(),hashes.SHA512())
  assert digs[0][1]==digest,'content digest mismatch'
  cert=x509.load_der_x509_certificate(certs[0]);assert cert.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)==pub
  fp=cert.fingerprint(hashes.SHA256()).hex();assert fp=='23e8720f08b5975b28fdda85586ab1e7e8422c64082e6a0e221f657c0b7a4e15'
  result['schemes'][str(version)]={'RSA_signature_verified':True,'content_digest_verified':True,'certificate_sha256':fp,'sdk':sdk,'attributes':[hex(struct.unpack_from('<I',x)[0]) for x in attrs]}
 return result
if __name__=='__main__':
 import sys
 for p in sys.argv[1:]:print(json.dumps(verify(p),indent=2))
