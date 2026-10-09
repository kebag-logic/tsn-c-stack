#!/usr/bin/env python3
"""Export selected execution receipts, normalizing locations only."""
import argparse
import hashlib
import json
from pathlib import Path
import re

p=argparse.ArgumentParser()
p.add_argument('checkout',type=Path)
p.add_argument('packet',type=Path)
p.add_argument('--location-map',type=Path,required=True,
               help='Unpublished JSON map from local prefixes to public placeholders')
a=p.parse_args()
root,packet=a.checkout.resolve(),a.packet.resolve()
locations=json.loads(a.location_map.read_text())
records=[]
def export(src,dst):
    if not src.is_file(): return
    data=src.read_bytes()
    text=data.decode('utf-8')
    text=text.replace(str(root),'$CHECKOUT').replace(str(packet),'$PACKET')
    for prefix,label in sorted(locations.items(),key=lambda item:-len(item[0])):
        text=text.replace(prefix,label)
    text=text.replace(str(Path.home()), '$USER')
    text=re.sub(r'/(?:home|Users)/[^/\s]+', '$USER', text)
    out=text.encode()
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_bytes(out)
    records.append({'source':str(src.relative_to(packet)),
                    'published':str(dst.relative_to(packet)),
                    'raw_sha256':hashlib.sha256(data).hexdigest(),
                    'published_sha256':hashlib.sha256(out).hexdigest(),
                    'location_normalized':data!=out})
for name,label in [('gates','initial'),('gates-clang18','clang18')]:
    base=packet/'scratch'/name
    for f in base.glob('*'):
        if f.suffix in ('.log','.rc','.json'):
            export(f,packet/'receipts'/label/f.name)
    for f in (base/'linux').glob('*'):
        if f.suffix in ('.log','.rc','.json'):
            export(f,packet/'receipts'/label/'validate'/f.name)
    for f in (base/'linux/mutations').rglob('*.xml'):
        export(f,packet/'receipts'/label/'mutations'/f.relative_to(base/'linux/mutations'))
    for filename in ['results.json','message-markers.json']:
        export(base/'linux/mutations'/filename,packet/'receipts'/label/'mutations'/filename)
    for f in (base/'linux/graphs').glob('*.svg'):
        export(f,packet/'receipts'/label/'graphs'/f.name)
    for f in (base/'rv32').rglob('*'):
        if f.name=='results.json' or f.suffix in ('.log','.map'):
            export(f,packet/'receipts'/label/'rv32'/f.relative_to(base/'rv32'))
for f in (packet/'scratch/claims').rglob('*'):
    rel=f.relative_to(packet/'scratch/claims')
    if len(rel.parts)<=2 and f.suffix in ('.json','.log','.rc'):
        export(f,packet/'receipts/claims'/rel)
for folder,files in [('quality-evidence',['gates.json','coverage.log','mutation.log','graphs.log','traceability.log','mutations/results.json']),
                     ('rv32-evidence',['results.json','debug/smoke.log','release/smoke.log'])]:
    for file in files:
        export(packet/'scratch/hosted'/folder/file,packet/'receipts/hosted'/folder/file)
(packet/'receipts/NORMALIZATION.json').write_text(json.dumps({
    'policy':'Only local machine locations are normalized. Result fields, diagnostics, counts and return codes are retained. Original files remain under scratch.',
    'files':records},indent=2)+'\n')
print('Exported',len(records),'receipts.')
