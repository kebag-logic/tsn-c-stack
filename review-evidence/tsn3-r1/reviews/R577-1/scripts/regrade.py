#!/usr/bin/env python3
"""Independently regrade every registered plant from saved assertion XML."""
import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

p=argparse.ArgumentParser()
p.add_argument('plants',type=Path)
p.add_argument('campaign',type=Path)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
plants=json.loads(a.plants.read_text())
results=json.loads((a.campaign/'results.json').read_text())
by_name={r['name']:r for r in results}
assert len(by_name)==len(results)==len(plants)
assert set(by_name)=={m['name'] for m in plants}
begin,end=json.loads((a.campaign/'message-markers.json').read_text())
pattern=re.compile(r'\n'+re.escape(begin)+r'\n(.*?)\n'+re.escape(end)+r'\n',re.S)
rows=[]
for m in plants:
    result=by_name[m['name']]
    assert result['status']=='CAUGHT' and result['rc']==1
    cases={}
    xmls=sorted((a.campaign/m['name']).glob('*.xml'))
    assert xmls
    for file in xmls:
        doc=ET.parse(file).getroot()
        nodes=list(doc.iter('testcase'))
        assert len(nodes)==int(doc.get('tests'))>0
        assert int(doc.get('errors'))==int(doc.get('disabled'))==0
        assert int(doc.get('failures'))==sum(bool(n.findall('failure')) for n in nodes)
        for node in nodes:
            name=(file.stem,node.get('classname')+'.'+node.get('name'))
            assert name not in cases
            assert node.get('status')=='run' and node.get('result')=='completed'
            assert not node.findall('skipped') and not node.findall('error')
            messages='\n'.join(n.get('message','') for n in node.findall('failure'))
            cases[name]='\n'.join(pattern.findall(messages))
    required=[]
    default_arm='maap_debug' if any(k['test'].startswith('MaapDebug.') for k in m['kills']) else Path(m['path']).stem
    for kill in m['kills']:
        arm=kill.get('arm',default_arm)
        selected=[n for n in cases if n[0]==arm and n[1].startswith(kill['test'])] if kill['test'].endswith('/') else [(arm,kill['test'])]
        assert selected and all(n in cases for n in selected)
        matched=[n for n in selected if kill['needle'] in cases[n]]
        assert matched, (m['name'],kill['test'])
        required.append(dict(test=kill['test'],selected=len(selected),matched=len(matched),needle=kill['needle']))
    rows.append(dict(name=m['name'],status='CAUGHT',required_killers=required))
out=dict(plants=len(rows),required_killer_entries=sum(len(r['required_killers']) for r in rows),
         caught=len(rows),escaped=0,errors=0,results=rows)
a.output.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='results'}))
