#!/usr/bin/env python3
"""Compare comment-free code and independently audit tracked bytes/modes/index."""
import hashlib,json,os,pathlib,re,stat,subprocess,sys
repo,packet=map(lambda x:pathlib.Path(x).resolve(),sys.argv[1:3])
def git(*args):return subprocess.check_output(["git","-C",str(repo),*args])
pattern=re.compile(r"//[^\n]*|/\*.*?\*/|\"(?:\\.|[^\"\\])*\"|\x27(?:\\.|[^\x27\\])*\x27",re.S)
def strip(s):return pattern.sub(lambda m:"\n"*m[0].count("\n") if m[0].startswith("/") else m[0],s)
comparisons=[]
for path in ["src/acmp.c","include/acmp.h"]:
 a=(repo/path).read_text();b=(packet/"receipts"/("upstream-"+pathlib.Path(path).name)).read_text()
 aa=[s.rstrip() for s in strip(a).splitlines()];bb=[s.rstrip() for s in strip(b).splitlines()]
 comparisons.append({"path":path,"head_lines":len(aa),"reference_lines":len(bb),"noncomment_line_identity":aa==bb,"head_sha256":hashlib.sha256(a.encode()).hexdigest(),"reference_sha256":hashlib.sha256(b.encode()).hexdigest()})
assert all(r["noncomment_line_identity"] for r in comparisons)
rows=[];links=[]
for item in git("ls-tree","-rz","HEAD").split(b"\0"):
 if not item:continue
 meta,name=item.split(b"\t",1);mode,kind,oid=meta.decode().split();name=os.fsdecode(name)
 if mode=="160000":links.append({"path":name,"commit":oid});continue
 p=repo/name
 content=os.readlink(p).encode() if mode=="120000" else p.read_bytes()
 actual=hashlib.sha1(b"blob "+str(len(content)).encode()+b"\0"+content).hexdigest()
 gotmode="120000" if p.is_symlink() else ("100755" if p.stat().st_mode & stat.S_IXUSR else "100644")
 assert actual==oid and gotmode==mode,(name,actual,oid,gotmode,mode)
 rows.append({"path":name,"mode":mode,"blob":oid,"bytes":len(content)})
head=git("rev-parse","HEAD").decode().strip();tree=git("rev-parse","HEAD^{tree}").decode().strip();index=git("write-tree").decode().strip()
assert head=="f3dc2ae5bad02aa05a504b43c207e8b304d2bed5"
assert tree==index=="d4ec359c00b7b34070e2b01d297607327260550a"
assert not git("status","--porcelain=v1")
r={"head":head,"tree":tree,"index_tree":index,"status":"clean","tracked_count":len(rows),"gitlinks":links,"comparisons":comparisons,"tracked_files":rows}
(packet/"receipts/final-integrity.json").write_text(json.dumps(r,indent=2)+"\n")
print(json.dumps({k:v for k,v in r.items() if k!="tracked_files"},indent=2))
