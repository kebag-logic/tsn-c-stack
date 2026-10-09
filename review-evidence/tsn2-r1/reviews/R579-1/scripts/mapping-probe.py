#!/usr/bin/env python3
"""Compare the portable mapper with the pinned source hexadecimal parser.
Usage: python3 mapping-probe.py REPO SOURCE_BUILDER AX7101_SOURCE OUTPUT
The two authority files come from milan-fpga revision
5603c353137e90c1fa95429f6d00ef7a2298d9ee.
Only pure scalar parsing functions are extracted; no builder bank runs.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any
repo, builder, source, output = map(Path, sys.argv[1:])
sys.path.insert(0, str(repo / "scripts"))
import entity_yaml as entity
from milan_entity import project
names = {"_hex_text", "_eui64", "_declared_uint", "_model_id", "_vendor_oui"}
nodes = [n for n in ast.parse(builder.read_text()).body if isinstance(n, ast.FunctionDef) and n.name in names]
assert len(nodes) == len(names)
ctx = dict(Any=Any, ConfigError=ValueError, EUI64_MAX=(1 << 64)-1,
           MODEL_ID_OUI=0x001BC5, HEX_TEXT=re.compile(r"(?:0[xX])?([0-9A-Fa-f](?:_?[0-9A-Fa-f])*)"))
exec(compile(ast.Module(body=nodes, type_ignores=[]), "pinned-source-scalar-parsers", "exec"), ctx)
doc = entity.load(source)
fixture = json.loads((repo / "configs/compat/ax7101.json").read_text())
model, caps = 0x001BC5C1935893E1, 0xC588
baseline = project(doc, model, caps)
assert baseline == entity.load(repo / "configs/ax7101.yaml")
assert len(source.read_bytes()) == fixture["source_bytes"]
assert hashlib.sha256(source.read_bytes()).hexdigest() == fixture["source_sha256"]
results=[]
variants=[("entity_id", "1234567890", "_eui64", 64),
          ("entity_id", "020000FFFE000001", "_eui64", 64),
          ("entity_model_id", "001BC5C1935893E1", "_model_id", 64),
          ("model_id_pin", "001BC5C1935893E1", "_model_id", 64),
          ("vendor_oui", "0x001BC5", "_declared_uint", 24),
          ("entity_capabilities", "0x0000C588", "_declared_uint", 32)]
for field,value,parser,bits in variants:
    changed=copy.deepcopy(doc)
    changed["entity"][field]=value
    expected=ctx[parser](value,bits,"entity."+field) if parser=="_declared_uint" else ctx[parser](value,"entity."+field)
    if field=="vendor_oui": assert expected==ctx["_vendor_oui"](changed["entity"])==model>>40
    if field=="entity_capabilities": assert expected==caps
    row=dict(field=field, input=value, source_expected=f"0x{expected:x}")
    try:
        mapped=project(changed,model,caps)
        actual=entity.validate(mapped)["entity_id"] if field=="entity_id" else mapped["identity"]["model_id"]
        row.update(mapper="accepted",actual=f"0x{actual:x}",matches=actual==expected)
    except entity.Invalid as e:
        row.update(mapper="refused",diagnostic=str(e),matches=False)
    results.append(row)
assert all(not r["matches"] for r in results)
report=dict(source_revision=fixture["revision"],source_path=fixture["source"],
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            builder_sha256=hashlib.sha256(builder.read_bytes()).hexdigest(),
            baseline_mapping="PASS", controls=results)
output.write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
