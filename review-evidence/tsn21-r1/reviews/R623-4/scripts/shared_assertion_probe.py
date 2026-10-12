#!/usr/bin/env python3
import json, os, shutil, subprocess, sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]; root=Path(sys.argv[1]).resolve();w=P/"scratch/shared-assertion";w.mkdir(parents=True,exist_ok=True)
for name in ("scripts","src","include","tests","examples"):
 shutil.copytree(root/name,w/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns("__pycache__"))
h=(w/"include/acmp.h").read_text();s=(w/"src/acmp.c").read_text();t=(w/"tests/test_acmp.cpp").read_text();m=json.loads((w/"tests/mutations.json").read_text())
h=h.replace("struct acmp_sink {","struct acmp_sink {\n\tbool published_future;")
s=s.replace("\tmemset(s, 0, sizeof *s);","\tbool published_future = s->published_future;\n\tmemset(s, 0, sizeof *s);",1)
s=s.replace("\ts->published_bound = published_bound;","\ts->published_future = published_future;\n\ts->published_bound = published_bound;",1)
start=t.index("TEST_F(AcmpCore, A31StoreResetOfABoundStoppedSinkPublishesItsWithdrawal)")
end=t.index("\n}",start)+2
case=t[start:end]
case=case.replace("    fk.clear();","    a.sinks[0].published_future = true;\n    fk.clear();")
old="    ASSERT_EQ(fk.pubs.size(), 1u)\n        << \"A31 the bound cache survives reset to publish the stopped binding withdrawal\";"
new="    ASSERT_TRUE(fk.pubs.size() == 1u && a.sinks[0].published_future)\n        << \"A31 the bound cache survives reset to publish the stopped binding withdrawal\"\n        << \"A31 future cache also survives the same reset\";"
assert case.count(old)==1
case=case.replace(old,new);t=t[:start]+case+t[end:]
m.append({"name":"acmp-publish-reset-future-cache","path":"src/acmp.c","old":"\ts->published_future = published_future;\n","new":"\t(void)published_future;\n","kills":[{"test":"AcmpCore.A31StoreResetOfABoundStoppedSinkPublishesItsWithdrawal","needle":"A31 future cache also survives the same reset"}],"original_tests":["AcmpCore.A31StoreResetOfABoundStoppedSinkPublishesItsWithdrawal"]})
for f,data in [("include/acmp.h",h),("src/acmp.c",s),("tests/test_acmp.cpp",t),("tests/mutations.json",json.dumps(m,indent=2)+"\n")]: (w/f).write_text(data)
R=P/"receipts/shared-assertion";R.mkdir(parents=True,exist_ok=True)
import difflib
(R/"probe.diff").write_text("".join("".join(difflib.unified_diff((root/f).read_text().splitlines(True),(w/f).read_text().splitlines(True),fromfile="head/"+f,tofile="probe/"+f)) for f in ("include/acmp.h","src/acmp.c","tests/test_acmp.cpp","tests/mutations.json")))
env=os.environ.copy();env.update(TSN_CLANG=os.environ.get("TSN_CLANG","clang-18"),PYTHONDONTWRITEBYTECODE="1",TMPDIR=str(P/"scratch"))
results=[]
for name,cmd in [("cache",[sys.executable,"-O","scripts/check_acmp_cache.py"]),("needles",[sys.executable,"scripts/needle_audit.py"]),("mutation",[sys.executable,"scripts/mutation.py","--work",str(P/"scratch/shared-mutations"),"--jobs","8","--select","acmp-publish-reset-"])]:
 with (R/(name+".log")).open("w") as f:r=subprocess.run(cmd,cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=540)
 (R/(name+".rc")).write_text(str(r.returncode)+"\n");results.append({"step":name,"rc":r.returncode}); print(json.dumps(results[-1]),flush=True)
(P/"receipts/shared-assertion/results.json").write_text(json.dumps(results,indent=2)+"\n")
if (P/"scratch/shared-mutations/results.json").exists():
 shutil.copy(P/"scratch/shared-mutations/results.json",R/"mutation-results.json")
 for f in (P/"scratch/shared-mutations").glob("*/*.xml"):
  if "bound" in f.parent.name or "future" in f.parent.name:shutil.copy(f,R/(f.parent.name+"-"+f.name))
