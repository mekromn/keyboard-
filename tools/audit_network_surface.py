#!/usr/bin/env python3
"""Contextual static inventory of Meboard outbound-network construction.

The report associates URL/domain literals and transport API calls with class and
source names, manifest registrations, and descriptor inbounds. A string hit is
not treated as an active connection; this is triage for physical removal while
preserving user-triggered dictation, GIF/search, translation, and model-download
features.
"""
from __future__ import annotations
import argparse,json,re
from collections import defaultdict
from pathlib import Path

CLASS_RE=re.compile(r'^\.class[^\n]* L([^;]+);',re.M)
SOURCE_RE=re.compile(r'^\.source\s+"([^"]+)"',re.M)
REF_RE=re.compile(r'L([A-Za-z0-9_$/]+);')
URL_RE=re.compile(r'(?i)\bhttps?://[^\s"<>]+')
DOMAIN_RE=re.compile(r'(?i)(?<![A-Za-z0-9_.-])(?:[A-Za-z0-9-]+\.)+(?:com|net|org|dev|app|googleapis)\b')
NETWORK_API=re.compile(r'(?i)(?:HttpURLConnection|URLConnection;->connect|CronetEngine|newUrlRequest|UrlRequest|OkHttpClient|Retrofit|grpc|ManagedChannel|Socket;->connect|SSLSocket|WebSocket|DownloadManager|HttpClient)')
BACKGROUND=re.compile(r'(?i)(clearcut|primes|phenotype|telemetry|analytics|metric|logging|daily.?ping|federat|training.?cache|diagnostic|crash|survey|feedback)')
USER_FEATURE=re.compile(r'(?i)(dictation|speech|voice|tenor|gif|sticker|translate|translation|download|language.?pack|model.?pack|emoji|search|handwriting|cloud.?suggest)')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('root',type=Path,nargs='?',default=Path('/mnt/data/meboard_work/buildtree'));ap.add_argument('--json',type=Path);a=ap.parse_args()
 root=a.root
 files={};texts={};sources={}
 for p in root.glob('smali*/**/*.smali'):
  t=p.read_text(errors='ignore');m=CLASS_RE.search(t)
  if not m:continue
  c=m.group(1);files[c]=p;texts[c]=t;sm=SOURCE_RE.search(t);sources[c]=sm.group(1) if sm else ''
 rev=defaultdict(set)
 for c,t in texts.items():
  for d in set(REF_RE.findall(t))-{c}:
   if d in texts:rev[d].add(c)
 manifest=(root/'AndroidManifest.xml').read_text(errors='ignore') if (root/'AndroidManifest.xml').is_file() else ''
 findings=[]
 for c,t in texts.items():
  urls=sorted(set(URL_RE.findall(t)));domains=sorted(set(DOMAIN_RE.findall(t)))
  api=[]
  for n,line in enumerate(t.splitlines(),1):
   if NETWORK_API.search(line):api.append({'line':n,'text':line.strip()[:500]})
  if not urls and not domains and not api:continue
  evidence=' '.join([c,sources[c],*urls,*domains,*[x['text'] for x in api]])
  if BACKGROUND.search(evidence):classification='background_or_reporting'
  elif USER_FEATURE.search(evidence):classification='user_feature_candidate'
  else:classification='unclassified'
  dotted=c.replace('/','.')
  findings.append({'class':c,'source':sources[c],'file':str(files[c].relative_to(root)),'classification':classification,'urls':urls,'domains':domains,'network_api_calls':api,'inbound_classes':sorted(rev[c]),'registered_in_manifest':(c in manifest or dotted in manifest)})
 # Native printable URL/domain strings are reported separately without implying reachability.
 native=[];printable=re.compile(rb'[\x20-\x7e]{5,}')
 for p in root.glob('lib/**/*.so'):
  rows=[]
  data=p.read_bytes()
  for m in printable.finditer(data):
   s=m.group().decode('utf-8','replace')
   if URL_RE.search(s) or DOMAIN_RE.search(s):rows.append({'offset':m.start(),'offset_hex':hex(m.start()),'text':s[:1000]})
  if rows:native.append({'file':str(p.relative_to(root)),'matches':rows})
 result={'root':str(root),'java_smali_findings':findings,'counts':dict(defaultdict(int)),'native_findings':native}
 counts=defaultdict(int)
 for f in findings:counts[f['classification']]+=1
 result['counts']=dict(counts)
 encoded=json.dumps(result,indent=2,sort_keys=True)
 if a.json:a.json.write_text(encoded+'\n')
 print(encoded)
if __name__=='__main__':main()
