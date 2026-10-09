#!/usr/bin/env python3
"""Collect completed target receipts and independently verify named mutations.
Usage: python3 collect-receipts.py REPO PACKET
Only local checkout/work paths are normalized in publishable log copies;
original bytes remain in scratch and their SHA-256 hashes are recorded.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET
repo,p=map(Path,sys.argv[1:])
v=p/"scratch/validation"
r=p/"scratch/rv32"
raw=p/"scratch/raw-receipts";raw.mkdir(exist_ok=True)
receipts=p/"receipts"
replacements=[(str(p),"<packet>"),(str(repo),"<repo>")]
records=[]
def save(src,dest):
 data=src.read_bytes()
 text=data.decode()
 for old,new in replacements: text=text.replace(old,new)
 text=re.sub(r"comment lexer: .*/(clang(?:-\d+)?)", r"comment lexer: <pinned-bin>/\1", text)
 dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_text(text)
 records.append(dict(receipt=str(dest.relative_to(p)),original_sha256=hashlib.sha256(data).hexdigest(),
                     published_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),paths_normalized=data!=dest.read_bytes()))
for src in sorted(v.glob("*.log"))+sorted(v.glob("*.rc"))+[v/"gates.json",v/"conditionals/results.json",v/"mutations/results.json",v/"mutations/message-markers.json"]:
 save(src,receipts/"validation"/src.relative_to(v))
for src in [r/"results.json",*sorted(r.glob("*/*.log"))]: save(src,receipts/"rv32"/src.relative_to(r))
for src in sorted((v/"graphs").glob("*.svg")): save(src,receipts/"graphs"/src.name)
results=json.loads((v/"mutations/results.json").read_text())
plants=json.loads((repo/"tests/mutations.json").read_text())
assert len(results)==len(plants)==330
begin,end=json.loads((v/"mutations/message-markers.json").read_text())
byname={x["name"]:x for x in results}
count=0
for plant in plants:
 row=byname[plant["name"]]
 assert row["status"]=="CAUGHT" and row["rc"]==1 and row["tests"]>0
 for kill in plant["kills"]:
  found=False
  for xmlpath in (v/"mutations"/plant["name"]).glob("*.xml"):
   if "arm" in kill and xmlpath.stem != kill["arm"]: continue
   root=ET.parse(xmlpath).getroot()
   assert int(root.attrib["tests"])>0 and not int(root.attrib.get("disabled",0))
   for case in root.iter("testcase"):
    assert case.attrib.get("result")=="completed"
    name=case.attrib["classname"]+"."+case.attrib["name"]
    target=kill["test"]
    if not (name.startswith(target) if target.endswith("/") else name==target): continue
    for failure in case.findall("failure"):
     streams=re.findall(re.escape(begin)+r"(.*?)"+re.escape(end),failure.attrib.get("message",""),re.S)
     if any(kill["needle"] in msg for msg in streams): found=True
  assert found,(plant["name"],kill)
  count+=1
for name in ["entity-wrong-count","entity-swapped-interface","entity-dropped-field"]:
 for src in (v/"mutations"/name).glob("*.xml"):
  xml=ET.parse(src).getroot(); assert int(xml.attrib["tests"])>0 and int(xml.attrib["failures"])>0
  assert all(t.attrib.get("result")=="completed" for t in xml.iter("testcase"))
  save(src,receipts/"entity-mutations"/name/src.name)
 save(v/"mutations"/name/"run.log",receipts/"entity-mutations"/name/"run.log")
summary=dict(gates=len(json.loads((v/"gates.json").read_text())),
             all_gates_zero=all(x["rc"]==0 for x in json.loads((v/"gates.json").read_text())),
             caught=len(results),named_assertions_verified=count,
             entity_plants=[{k:byname[n][k] for k in ("name","status","rc","tests")} for n in ["entity-wrong-count","entity-swapped-interface","entity-dropped-field"]])
(receipts/"verification-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
(receipts/"receipt-provenance.json").write_text(json.dumps(records,indent=2)+"\n")
print(json.dumps(summary,indent=2))
