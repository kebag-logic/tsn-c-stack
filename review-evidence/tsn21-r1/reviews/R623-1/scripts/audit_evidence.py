#!/usr/bin/env python3
"""Check exact-head hosted receipts and regrade every published mutation XML."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

p=argparse.ArgumentParser(); p.add_argument('root',type=Path); a=p.parse_args()
root=a.root.resolve(); packet=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
import mutation
head='2dcbe91ead981591d5bfb652f6616f6edb325875'
artifacts=json.loads((packet/'scratch/hosted-artifacts.json').read_text())['artifacts']
for item in artifacts:
    assert item['workflow_run']['head_sha']==head
    name='quality' if item['name']=='quality-evidence' else 'rv32'
    assert 'sha256:'+hashlib.sha256((packet/f'scratch/hosted-{name}.zip').read_bytes()).hexdigest()==item['digest']
quality=packet/'scratch/hosted-quality'
gates=json.loads((quality/'gates.json').read_text())
assert len(gates)==25 and all(r['rc']==0 for r in gates)
jobs=json.loads((packet/'receipts/hosted-jobs.json').read_text())['jobs']
assert len(jobs)==2 and all(j['conclusion']=='success' for j in jobs)
assert all(s['conclusion']=='success' for j in jobs for s in j['steps'])
summary={'head':head,'hosted_run':38186240742,'artifact_digests_verified':True,
         'executed_jobs':[{'id':j['id'],'name':j['name'],'conclusion':j['conclusion']} for j in jobs],
         'skipped_job_steps':0,'passed_gate_commands':len(gates),'campaigns':[]}
plants=json.loads((root/'tests/mutations.json').read_text())
for label,work,selected in [('hosted',quality/'mutations',plants),
                            ('reviewer',packet/'scratch/mutations',[m for m in plants if m['name'].startswith('acmp-publish')])]:
    mutation.MESSAGE_MARKERS=tuple(json.loads((work/'message-markers.json').read_text()))
    records=json.loads((work/'results.json').read_text())
    assert len(records)==len(selected) and {r['name'] for r in records}=={m['name'] for m in selected}
    assert all(r['status']=='CAUGHT' and r['rc']==1 for r in records)
    instances=0
    for m in selected:
        default='maap_debug' if any(k['test'].startswith('MaapDebug.') for k in m['kills']) else Path(m['path']).stem
        arms=sorted({k.get('arm',default) for k in m['kills']})
        assert {f.stem for f in (work/m['name']).glob('*.xml')}==set(arms)
        for arm in arms:
            failures={}
            kills=[k for k in m['kills'] if k.get('arm',default)==arm]
            f=work/m['name']/(arm+'.xml')
            doc=ET.parse(f).getroot(); cases=list(doc.iter('testcase'))
            assert int(doc.get('tests'))==len(cases)>0
            assert int(doc.get('disabled'))==0 and int(doc.get('errors'))==0
            assert int(doc.get('failures'))==sum(bool(c.findall('failure')) for c in cases)
            names=[c.get('classname')+'.'+c.get('name') for c in cases]
            assert len(set(names))==len(names)
            patterns=[k['test']+('*' if k['test'].endswith('/') else '') for k in kills]
            expected=set(mutation.registered(packet/'scratch/mutations/baseline'/arm,patterns))
            assert set(names)==expected,(m['name'],arm,'registration mismatch')
            for c in cases:
                assert c.get('status')=='run' and c.get('result')=='completed'
                assert not c.findall('skipped') and not c.findall('error')
                messages=[x.get('message','') for x in c.findall('failure')]
                if messages: failures[c.get('classname')+'.'+c.get('name')]='\n'.join(messages)
            instances+=len(cases)
            assert all(mutation.matches(k,failures) for k in kills),(m['name'],arm)
    summary['campaigns'].append({'source':label,'plants':len(selected),'named_assertions_regraded':True,'test_instances':instances,'skips':0})
(packet/'receipts/evidence-audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
