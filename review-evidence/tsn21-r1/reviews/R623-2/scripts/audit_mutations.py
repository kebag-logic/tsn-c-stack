#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Independently regrade campaign XML by registration, arm and owned message."""
import json,pathlib,sys,xml.etree.ElementTree as ET
root,work,out=map(pathlib.Path,sys.argv[1:]);plants=json.load(open(root/"tests/mutations.json"));results=json.load(open(work/"results.json"));markers=json.load(open(work/"message-markers.json"))
assert len(results)==len(plants)==340 and {x["name"] for x in results}=={x["name"] for x in plants}
assert all(x["status"]=="CAUGHT" and x["rc"]==1 for x in results)
def read(path):
 doc=ET.parse(path).getroot();cases=list(doc.iter("testcase")); names=[c.attrib["classname"]+"."+c.attrib["name"] for c in cases]
 assert doc.tag=="testsuites" and len(cases)==int(doc.attrib["tests"]) and len(set(names))==len(names)
 assert int(doc.attrib["errors"])==0 and int(doc.attrib["disabled"])==0
 assert int(doc.attrib["failures"])==sum(bool(c.findall("failure")) for c in cases)
 assert all(c.get("status")=="run" and c.get("result")=="completed" and not c.findall("skipped") and not c.findall("error") for c in cases)
 return dict(zip(names,cases))
def matches(pattern,name):return name.startswith(pattern) if pattern.endswith("/") else name==pattern
def owned(message):
 begin,end=("\n"+m+"\n" for m in markers);chunks=[]
 while begin in message:
  message=message.split(begin,1)[1];part,sep,message=message.partition(end);assert sep;chunks.append(part)
 return "\0".join(chunks)
baselines={p.stem:read(p) for p in (work/"baseline").glob("*.xml")}
assert len(baselines)==7 and all(not c.findall("failure") for b in baselines.values() for c in b.values())
checked=0;selected=0
for m in plants:
 module=pathlib.Path(m["path"]).stem
 default="maap_debug" if any(k["test"].startswith("MaapDebug.") for k in m["kills"]) else module
 arms={k.get("arm",default) for k in m["kills"]}
 for arm in arms:
  kills=[k for k in m["kills"] if k.get("arm",default)==arm];cases=read(work/m["name"]/(arm+".xml"))
  expected={n for n in baselines[arm] if any(matches(k["test"],n) for k in kills)}
  assert expected and set(cases)==expected,(m["name"],arm,"registration")
  for k in kills:
   assert any(matches(k["test"],n) and any(k["needle"] in owned(f.get("message","")) for f in c.findall("failure")) for n,c in cases.items()),(m["name"],k)
  selected+=len(cases)
 checked+=1
summary={"plants":checked,"caught":checked,"escaped":0,"errors":0,"baseline_instances":sum(map(len,baselines.values())),"selected_instances":selected,"skips":0,"complete_xml_and_registration":True,"all_required_owned_messages":True}
out.write_text(json.dumps(summary,indent=2)+"\n");print(summary)
