#!/usr/bin/env python3
"""Demonstrate the mapping defect through both public CLIs and compiled C.
Usage: python3 cli-identity-probe.py REPO SOURCE_YAML WORK RECEIPT
"""
import json
from pathlib import Path
import subprocess
import sys
import yaml
repo,source,work,receipt=map(Path,sys.argv[1:])
work.mkdir(parents=True,exist_ok=True)
doc=yaml.safe_load(source.read_text());doc["entity"]["entity_id"]="1234567890"
(work/"source.yaml").write_text(yaml.safe_dump(doc,sort_keys=False))
commands=[[sys.executable,str(repo/"scripts/milan_entity.py"),str(work/"source.yaml"),"--model-id","0x001BC5C1935893E1","--capabilities","0xC588","--output",str(work/"mapped.yaml")],
 [sys.executable,str(repo/"scripts/entity_yaml.py"),str(work/"mapped.yaml"),"--output",str(work)]]
records=[]
for command in commands:
 r=subprocess.run(command,text=True,capture_output=True);assert r.returncode==0,r.stderr
 records.append(dict(stage=Path(command[1]).name,rc=r.returncode,stdout=r.stdout,stderr=r.stderr))
(work/"identity.c").write_text('#include "entity_config.h"\n#include <stdio.h>\n#include <inttypes.h>\nint main(void) { printf("adp=%016" PRIx64 " acmp=%016" PRIx64 "\\n", entity_adp[0].entity_id, entity_acmp.entity_id); return 0; }\n')
command=["gcc","-std=c11","-Wall","-Wextra","-Werror","-I"+str(repo/"include"),str(work/"entity_config.c"),str(work/"identity.c"),"-o",str(work/"identity")]
r=subprocess.run(command,text=True,capture_output=True);assert r.returncode==0,r.stderr
r=subprocess.run([str(work/"identity")],text=True,capture_output=True);assert r.returncode==0
assert r.stdout=="adp=0000001234567890 acmp=0000001234567890\n"
records.append(dict(stage="compiled configuration",rc=r.returncode,stdout=r.stdout))
result=dict(input_entity_id="1234567890",source_expected="0000001234567890",actual="0000001234567890",commands=records)
receipt.write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))
