#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check tracked bytes, modes, index and gitlinks against the required tree."""
import hashlib,json,os,pathlib,stat,subprocess,sys
root,out=map(pathlib.Path,sys.argv[1:]);head="f3dc2ae5bad02aa05a504b43c207e8b304d2bed5";tree="d4ec359c00b7b34070e2b01d297607327260550a"
def git(*args):return subprocess.check_output(["git","-C",str(root),*args])
assert git("rev-parse","HEAD").decode().strip()==head
assert git("rev-parse","HEAD^{tree}").decode().strip()==tree
entries={};files=[];gitlinks=[]
for item in git("ls-tree","-rz","HEAD").split(b"\0"):
 if not item:continue
 meta,path=item.split(b"\t",1);mode,kind,oid=meta.decode().split();path=path.decode();entries[path]=(mode,oid)
 if mode=="160000":
  actual=git("-C",str(root/path),"rev-parse","HEAD").decode().strip();assert actual==oid;gitlinks.append({"path":path,"commit":oid});continue
 f=root/path;st=f.lstat()
 if mode=="120000":assert stat.S_ISLNK(st.st_mode);data=os.readlink(f).encode()
 else:
  assert stat.S_ISREG(st.st_mode);assert (mode=="100755")==bool(st.st_mode&0o111);data=f.read_bytes()
 blob=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest();assert blob==oid,path
 files.append({"path":path,"mode":mode,"blob":blob,"sha256":hashlib.sha256(data).hexdigest()})
index={}
for item in git("ls-files","--stage","-z").split(b"\0"):
 if not item:continue
 meta,path=item.split(b"\t",1);mode,oid,stage=meta.decode().split();assert stage=="0";index[path.decode()]=(mode,oid)
assert index==entries
assert git("write-tree").decode().strip()==tree
assert not git("status","--porcelain=v1","--untracked-files=all").strip()
assert subprocess.run(["git","-C",str(root),"symbolic-ref","-q","HEAD"],stdout=subprocess.DEVNULL).returncode==1
summary={"head":head,"tree":tree,"detached":True,"tracked_count":len(files),"all_bytes_modes_index_match":True,"gitlinks":gitlinks,"status_clean":True,"files":files}
out.write_text(json.dumps(summary,indent=2)+"\n");print({k:v for k,v in summary.items() if k!="files"})
