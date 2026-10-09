#!/usr/bin/env python3
"""Verify actual tracked bytes, file modes, index entries and gitlinks."""
import argparse,hashlib,json,os,pathlib,stat,subprocess
ap=argparse.ArgumentParser();ap.add_argument('source',type=pathlib.Path);a=ap.parse_args();source=a.source.resolve()
def git(*args):return subprocess.check_output(['git','-C',str(source),*args])
head=git('rev-parse','HEAD').decode().strip();tree=git('rev-parse','HEAD^{tree}').decode().strip();assert head=='663f14de4a07bb1a777282fdfc83d30fd03843d4';assert tree=='cff76b8564bc21ff16a57c2e32f4abe1b6d3e3e9'
index={}
for line in git('ls-files','--stage','-z').split(b'\0'):
 if not line:continue
 meta,name=line.split(b'\t');mode,sha,stage=meta.decode().split();assert stage=='0';index[name.decode()]=(mode,sha)
blobs=[];links=[]
for line in git('ls-tree','-rz','HEAD').split(b'\0'):
 if not line:continue
 meta,name=line.split(b'\t');mode,kind,sha=meta.decode().split();name=name.decode();assert index.pop(name)==(mode,sha)
 if mode=='160000':links.append({'path':name,'commit':sha});continue
 f=source/name;data=os.readlink(f).encode() if mode=='120000' else f.read_bytes();actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();actual_mode='120000' if f.is_symlink() else ('100755' if f.stat().st_mode & stat.S_IXUSR else '100644');assert(actual,actual_mode)==(sha,mode),(name,sha,actual)
 blobs.append({'path':name,'mode':mode,'blob':sha})
assert not index;assert not links,'No required gitlinks are expected at this source head'
unchanged={name:git('rev-parse','18d73783:'+name).decode().strip()==git('rev-parse','HEAD:'+name).decode().strip() for name in ['src','include','examples','cmake','CMakeLists.txt','.github']};assert all(unchanged.values())
print(json.dumps({'head':head,'tree':tree,'tracked_count':len(blobs),'tracked_blobs':blobs,'index_matches_head':True,'gitlinks':links,'unchanged_from_original_base':unchanged,'rtl_files':[b['path'] for b in blobs if pathlib.Path(b['path']).suffix in ['.sv','.v','.vhd','.vhdl']],'status':git('status','--porcelain=v1').decode()},indent=2))
