#!/usr/bin/env python3
"""Extract public dependency packages only beneath the packet scratch directory."""
import argparse, concurrent.futures, gzip, hashlib, json, pathlib, subprocess, urllib.request
ap=argparse.ArgumentParser();ap.add_argument('packet',type=pathlib.Path);a=ap.parse_args();p=a.packet.resolve();sdk=p/'scratch/sdk';sdk.mkdir(parents=True,exist_ok=True)
base='https://archive.ubuntu.com/ubuntu/'
names={'libstdc++-13-dev','libclang-rt-18-dev'}
records={}
for component in ['main','universe']:
 url=base+'dists/noble/'+component+'/binary-amd64/Packages.gz'
 data=urllib.request.urlopen(url).read()
 for block in gzip.decompress(data).decode().split('\n\n'):
  fields=dict(line.split(': ',1) for line in block.splitlines() if ': ' in line and not line.startswith(' '))
  if fields.get('Package') in names:records[fields['Package']]=fields
assert set(records)==names
out=[]
def get(item):
 name,f=item;data=urllib.request.urlopen(base+f['Filename']).read();assert hashlib.sha256(data).hexdigest()==f['SHA256'];deb=sdk/(name+'.deb');deb.write_bytes(data);root=sdk/'root';root.mkdir(exist_ok=True);member=next(s for s in subprocess.check_output(['ar','t',str(deb)],text=True).splitlines() if s.startswith('data.tar'));payload=subprocess.check_output(['ar','p',str(deb),member]);subprocess.run(['tar','--zstd' if member.endswith('.zst') else '-J','-x','--no-same-owner','-C',str(root)],input=payload,check=True);return {'package':name,'version':f['Version'],'url':base+f['Filename'],'sha256':f['SHA256']}
# Extraction is sequential because packages share directory entries.
for item in records.items():out.append(get(item))
(p/'receipts/sdk-packages.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
