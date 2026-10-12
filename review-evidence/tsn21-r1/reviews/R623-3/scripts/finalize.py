#!/usr/bin/env python3
"""Normalize local path prefixes, preserve raw logs privately, and hash publications."""
import hashlib,json,pathlib,shutil,sys
repo,packet=map(lambda s:pathlib.Path(s).resolve(),sys.argv[1:3]);raw=packet/"scratch/raw-receipts";rows=[]
replacements=[(str(packet).encode(),b"$REVIEW_PACKET"),(str(repo).encode(),b"$SOURCE")]
if len(sys.argv)>3:replacements.append((str(pathlib.Path(sys.argv[3]).resolve()).encode(),b"$DEPENDENCIES"))
for category in ["local","cache-probes","rv32-cache-controls"]:
 for path in sorted((packet/"receipts"/category).rglob("*")):
  if not path.is_file():continue
  if "CMakeFiles" in path.parts:
   dest=raw/path.relative_to(packet);dest.parent.mkdir(parents=True,exist_ok=True);shutil.move(path,dest);continue
  before=path.read_bytes();after=before
  for old,new in replacements:after=after.replace(old,new)
  if after!=before:
   rel=path.relative_to(packet);dest=raw/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(before);path.write_bytes(after)
   rows.append({"file":str(rel),"original_sha256":hashlib.sha256(before).hexdigest(),"published_sha256":hashlib.sha256(after).hexdigest(),"change":"local absolute path prefixes only"})
(packet/"receipts/path-normalization.json").write_text(json.dumps(rows,indent=2)+"\n")
files=[f for f in packet.rglob("*") if f.is_file() and "scratch" not in f.relative_to(packet).parts and f.name not in ["REPORT.md","MANIFEST.sha256"]]
manifest="".join(hashlib.sha256(f.read_bytes()).hexdigest()+"  "+str(f.relative_to(packet))+"\n" for f in sorted(files))
(packet/"MANIFEST.sha256").write_text(manifest)
assert (packet/"REPORT.md").read_text().splitlines()[0]=="[R623] NEGATIVE - exact head f3dc2ae5bad02aa05a504b43c207e8b304d2bed5"
assert (packet/"REPORT.md").read_text().splitlines()[-1]=="R623-3 FINISHED"
assert "SKELETON" not in (packet/"REPORT.md").read_text()
proof=json.loads((packet/"receipts/independent-verdict-record.json").read_text());assert proof["sha256"]==hashlib.sha256((packet/"receipts/independent-verdict.md").read_bytes()).hexdigest()
print(json.dumps({"publishable_files_listed":len(files),"path_normalized_receipts":len(rows),"independent_verdict_unchanged":True,"report_sha256":hashlib.sha256((packet/"REPORT.md").read_bytes()).hexdigest()},indent=2))
