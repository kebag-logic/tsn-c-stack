#!/usr/bin/env python3
"""Collect execution receipts with explicit host-location substitutions."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('--tools-prefix',type=Path,required=True)
a=p.parse_args()
packet=Path(__file__).resolve().parents[1]
scratch=packet/'scratch'; out=packet/'receipts'
replacements=[(str(packet),'$PACKET'),(str(a.source.resolve()),'$SOURCE'),
              (str(a.tools_prefix.resolve()),'$DEPENDENCIES')]
provenance=[]
def save(src,dst):
    raw=src.read_bytes(); text=raw.decode()
    for old,new in replacements: text=text.replace(old,new)
    published=text.encode(); dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(published)
    provenance.append(dict(receipt=str(dst.relative_to(packet)),raw_sha256=hashlib.sha256(raw).hexdigest(),
                           published_sha256=hashlib.sha256(published).hexdigest(),path_redacted=raw!=published))
for run in ['validation','rv32']:
    save(scratch/(run+'.raw.log'),out/'local'/(run+'.log'))
    directory=scratch/run
    for pattern in ['*.log','*.rc','*.json']:
        for file in directory.glob(pattern):save(file,out/'local'/run/file.name)
    if run=='rv32':
        for file in directory.glob('*/*.log'):save(file,out/'local'/run/file.relative_to(directory))
        for file in directory.glob('*/*.map'):save(file,out/'local'/run/file.relative_to(directory))
    else:
        for file in directory.glob('graphs/*.svg'):save(file,out/'local'/run/file.relative_to(directory))
        for kind in ['gcc','clang-sanitizers']:
            file=directory/kind/'Testing/Temporary/LastTest.log'
            save(file,out/'local'/run/(kind+'-instances.log'))
        campaign=directory/'mutations'
        for file in [campaign/'results.json',campaign/'message-markers.json',*campaign.glob('*/*.xml')]:
            save(file,out/'local/mutations'/file.relative_to(campaign))
save(a.source/'tests/mutations.json',out/'mutation-plants.json')
(out/'receipt-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
jobs=[]
for name,event in [('pr-jobs-final','pull_request'),('push-jobs-final','push')]:
    for j in json.loads((scratch/(name+'.json')).read_text())['jobs']:
        jobs.append({**{k:j[k] for k in ['id','run_id','name','head_sha','status','conclusion','started_at','completed_at','html_url']},
                     'event':event,'steps':[{k:s.get(k) for k in ['number','name','status','conclusion']} for s in j['steps']]})
(out/'hosted-jobs.json').write_text(json.dumps(jobs,indent=2)+'\n')
pr=json.loads((scratch/'pr19.json').read_text())
issue_file=out/'issue3.json'
if not issue_file.exists(): issue_file=scratch/'raw-issue3.json'
public=dict(observed_utc=datetime.now(timezone.utc).isoformat(),
            pr=dict(number=19,url=pr['html_url'],head=pr['head']['sha'],base=pr['base']['sha'],body=pr['body']),
            issue=json.loads(issue_file.read_text())['body'])
comments=[]
for file in ['issue3-comments-final','pr19-comments-final','pr19-reviews','pr19-review-comments']:
    records=json.loads((scratch/(file+'.json')).read_text())
    for c in records:
        item={k:c.get(k) for k in ['id','html_url','created_at','updated_at','state']}
        item['collection']=file
        if c['id']==6085778617:
            item['disposition']='Read after independent verdict; F1 retained as residue and S1 retained as suggestion.'
        else:
            body=c['body']
            for old,new in replacements: body=body.replace(old,new)
            item['body']=body
        comments.append(item)
public['comments']=comments
public['formal_reviews']=len(json.loads((scratch/'pr19-reviews.json').read_text()))
public['inline_review_comments']=len(json.loads((scratch/'pr19-review-comments.json').read_text()))
(out/'public-records.json').write_text(json.dumps(public,indent=2)+'\n')
print('Collected',len(provenance),'execution receipts and',len(jobs),'hosted jobs.')
