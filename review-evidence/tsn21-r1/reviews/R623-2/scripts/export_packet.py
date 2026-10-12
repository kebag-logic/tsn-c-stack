#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Export path-normalized text receipts and a publication checksum manifest.
Usage: export_packet.py PACKET CHECKOUT DEPENDENCY_PREFIX
Raw originals are retained only under scratch/raw-receipts.
"""
import hashlib,json,pathlib,re,shutil,sys
p,root,deps=map(lambda s:pathlib.Path(s).resolve(),sys.argv[1:]);raw=p/"scratch/raw-receipts";mapping=[]
replacements=[(str(p),"<packet>"),(str(root),"<source>"),(str(deps),"<dependencies>"),("/"+"home/runner/work/tsn-c-stack/tsn-c-stack","<hosted-source>")]
for f in sorted((p/"receipts").rglob("*")):
 if not f.is_file() or f.name=="export-map.json":continue
 rel=f.relative_to(p);backup=raw/rel;original=backup.read_bytes() if backup.exists() else f.read_bytes();text=original.decode()
 for old,new in replacements:text=text.replace(old,new)
 data=text.encode()
 if data!=original:
  backup=raw/rel;backup.parent.mkdir(parents=True,exist_ok=True)
  if not backup.exists():backup.write_bytes(original)
  f.write_bytes(data)
 mapping.append({"file":str(rel),"raw_sha256":hashlib.sha256(original).hexdigest(),"exported_sha256":hashlib.sha256(data).hexdigest(),"path_prefixes_normalized":data!=original})
(p/"receipts/export-map.json").write_text(json.dumps(mapping,indent=2)+"\n")
files=[p/"REPORT.md"]+[f for directory in [p/"scripts",p/"receipts"] for f in directory.rglob("*") if f.is_file()]
assert all("scratch" not in f.relative_to(p).parts for f in files)
for f in files:
 data=f.read_text();assert not re.search(r"/(?:home|data)/",data),f
assert (p/"REPORT.md").read_text().splitlines()[0]=="[R623] NEGATIVE - exact head f3dc2ae5bad02aa05a504b43c207e8b304d2bed5"
assert (p/"REPORT.md").read_text().splitlines()[-1]=="R623-2 FINISHED"
assert "SKELETON" not in (p/"REPORT.md").read_text()
(p/"MANIFEST.sha256").write_text("".join(hashlib.sha256(f.read_bytes()).hexdigest()+"  "+str(f.relative_to(p))+"\n" for f in sorted(files)))
print(json.dumps({"publishable_files":len(files),"bytes":sum(f.stat().st_size for f in files),"normalized_receipts":sum(x["path_prefixes_normalized"] for x in mapping),"scratch_excluded":True}))
