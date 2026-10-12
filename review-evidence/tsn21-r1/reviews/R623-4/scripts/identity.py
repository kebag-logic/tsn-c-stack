#!/usr/bin/env python3
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]; root=Path(sys.argv[1]).resolve();sys.path.insert(0,str(root/"scripts"))
os.environ["TSN_CLANG"]=os.environ.get("TSN_CLANG","clang-18")
from compiler_tokens import raw_tokens
rows=[]
for local,reference in [("src/acmp.c","acmp.c"),("include/acmp.h","acmp.h")]:
 data=(root/local).read_bytes();before=subprocess.check_output(["git","show","f3dc2ae5bad02aa05a504b43c207e8b304d2bed5:"+local],cwd=root);ref=(P/"receipts/authorities"/reference).read_text()
 def tokens(s):
  return [(k,v,line,at-s.rfind("\n",0,at)) for k,v,at,end,line in raw_tokens(s) if k!="comment" and not v.isspace()]
 a=tokens(data.decode());b=tokens(ref)
 row={"path":local,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"round2_bytes_equal":data==before,"reference_tokens":len(b),"head_tokens":len(a),"tokens_lines_columns_equal":a==b};rows.append(row);print(json.dumps(row));assert data==before and a==b
w=P/"scratch/object-identity";w.mkdir(parents=True,exist_ok=True);src=w/"src";src.mkdir(exist_ok=True);out=w/"out";out.mkdir(exist_ok=True)
cc=shutil.which("riscv64-unknown-elf-gcc") or shutil.which("riscv64-elf-gcc");assert cc
builtin=subprocess.check_output([cc,"-print-file-name=include"],text=True).strip()
base=["-march=rv32i","-mabi=ilp32","-ffreestanding","-fno-builtin","-nostdinc","-isystem",builtin,"-std=c11","-Wall","-Wextra","-Werror"]
sets={"debug-g0":["-DCTRL_REENTRY_ASSERT","-g0"],"debug":["-DCTRL_REENTRY_ASSERT","-g"],"release":["-DCTRL_REENTRY_ASSERT","-O3","-DNDEBUG"],"os":["-DCTRL_REENTRY_ASSERT","-Os"],"o2-noassert":["-O2"],"os-g3":["-Os","-g3"]}
objects=[]
for name,flags in sets.items():
 hashes=[];data=[]
 for side in ("head","reference"):
  shutil.copy(root/"include/wire.h",src/"wire.h")
  for f,local in [("acmp.c","src/acmp.c"),("acmp.h","include/acmp.h")]:shutil.copy(root/local if side=="head" else P/"receipts/authorities"/f,src/f)
  obj=out/(name+"-"+side+".o")
  subprocess.run([cc,"-Isrc","-I"+str(root/"examples/rv32/include"),*base,*flags,"-c","src/acmp.c","-o",str(obj)],cwd=w,check=True)
  data.append(obj.read_bytes());hashes.append(hashlib.sha256(data[-1]).hexdigest())
 row={"configuration":name,"extra_flags":flags,"raw_equal":data[0]==data[1],"sha256":hashes,"bytes":len(data[0])};objects.append(row);print(json.dumps(row));assert row["raw_equal"]
result={"head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip(),"files":rows,"compiler":subprocess.check_output([cc,"--version"],text=True).splitlines()[0],"common_flags":base,"objects":objects}
(P/"receipts/identity.json").write_text(json.dumps(result,indent=2)+"\n")
