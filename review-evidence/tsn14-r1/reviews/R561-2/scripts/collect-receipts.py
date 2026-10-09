#!/usr/bin/env python3
"""Collect text receipts with location redaction and original hashes."""
import argparse,hashlib,json,pathlib,re
ap=argparse.ArgumentParser();ap.add_argument('source',type=pathlib.Path);ap.add_argument('packet',type=pathlib.Path);ap.add_argument('--dependency-root',type=pathlib.Path);a=ap.parse_args();source=a.source.resolve();p=a.packet.resolve();w=p/'scratch';records=[]
replacements=[(str(p),'$PACKET'),(str(source),'$SOURCE')]
replacements.append((str(pathlib.Path.home()),'$USER_ROOT'))
if a.dependency_root: replacements.append((str(a.dependency_root.resolve()),'$DEPENDENCIES'))
def save(src,dest):
 data=src.read_bytes();text=data.decode();redacted=text
 for old,new in replacements:redacted=redacted.replace(old,new)
 redacted=re.sub(r'/home/[^/ \n]+', '$USER_ROOT',redacted)
 redacted=re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',redacted)
 dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(redacted)
 records.append({'file':str(dest.relative_to(p)),'raw_sha256':hashlib.sha256(data).hexdigest(),'published_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'location_or_terminal_normalization':data!=dest.read_bytes()})
for campaign in ['validate','baremetal']:
 for suffix in ['log','rc']:save(w/(campaign+'.'+suffix),p/'receipts'/(campaign+'.'+suffix))
 root=w/campaign
 for file in root.iterdir():
  if file.is_file() and file.suffix in ['.log','.rc','.json']:save(file,p/'receipts'/campaign/file.name)
 if campaign=='validate':
  for file in (root/'mutations').rglob('*.xml'):save(file,p/'receipts/validate'/file.relative_to(root))
  for name in ['results.json','message-markers.json']:save(root/'mutations'/name,p/'receipts/validate/mutations'/name)
  for file in (root/'graphs').glob('*.svg'):save(file,p/'receipts/validate/graphs'/file.name)
 else:
  for file in root.rglob('*.log'):save(file,p/'receipts/baremetal'/file.relative_to(root))
for file in (w/'probes').rglob('*'):
 if file.is_file() and file.parent.name!='build' and 'src-tree' not in file.parts and 'build' not in file.parts and file.suffix in ['.log','.json','.rc']:save(file,p/'receipts/probes'/file.relative_to(w/'probes'))
save(w/'toolchain.json',p/'receipts/toolchain.json')
for job in ['113866224073','113866224582']:
 save(w/('hosted-'+job+'.log'),p/'receipts/hosted'/('job-'+job+'.log'))
 save(w/('hosted-'+job+'.rc'),p/'receipts/hosted'/('job-'+job+'.rc'))
(p/'receipts/NORMALIZATION.json').write_text(json.dumps(records,indent=2)+'\n')
print('Collected',len(records),'receipts; result fields and exit codes preserved.')
