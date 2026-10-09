#!/usr/bin/env python3
"""Independently match pinned upstream rows and exercise every anchor control."""
import argparse,pathlib,json,re,sys,copy
ap=argparse.ArgumentParser();ap.add_argument('source',type=pathlib.Path);ap.add_argument('packet',type=pathlib.Path);a=ap.parse_args();source=a.source.resolve();p=a.packet.resolve();sys.path.insert(0,str(source/'scripts'));import requirement_records as rr
req=json.loads((source/'docs/requirements.json').read_text());cat=json.loads((source/'docs/requirement-origins.json').read_text());m=rr.source_ids();actual={}
for name,file in [('docs/reference/FR_NFR.md','authority-fr-nfr.md'),('REQUIREMENTS.md','authority-requirements.md')]:
 for n,line in enumerate((p/'receipts'/file).read_text().splitlines(),1):
  match=re.match(r'(?:\|\s*|[-]\s*)\*{0,2}((?:FR|NFR|REQ)-[A-Z]+-\d+[ab]?)(?=\*| |\|)',line)
  if match: actual['milan-fpga '+match[1]]=rr.SOURCE_BASE+name+'#L'+str(n)
assert len(actual)==114 and all(m[k]==v for k,v in actual.items())
assert not rr.validate(req,cat)
controls=[]
for i,row in enumerate(cat['rows']):
 moved=copy.deepcopy(cat);moved['rows'][i]['url']=cat['rows'][(i+1)%len(cat['rows'])]['url'];errors=rr.validate(req,moved);assert any('pinned ID anchor' in e for e in errors);controls.append({'origin':row['origin'],'errors':errors})
counts={method:sum(rr.method(r)==method for r in req if r['id'].startswith('MF')) for method in rr.METHODS}
result={'source_rows':len(actual),'decision_anchors':2,'all_match':True,'moved_anchor_controls':controls,'imported_methods':counts,'dispositions':{s:sum(r['disposition']==s for r in cat['rows']) for s in ['ported','port obligation','excluded']}}
(p/'receipts/anchor-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('Source rows:',len(actual),'Moved anchors caught:',len(controls));print(counts,result['dispositions'])
