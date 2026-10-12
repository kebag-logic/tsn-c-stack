#!/usr/bin/env python3
import copy, json, os, shutil, subprocess, sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]; root=Path(sys.argv[1]).resolve(); work=P/"scratch/cache-controls"; work.mkdir(parents=True,exist_ok=True)
for name in ("scripts","src","include","tests"):
 shutil.copytree(root/name,work/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns("__pycache__"))
header=(root/"include/acmp.h").read_text(); source=(root/"src/acmp.c").read_text(); tests=(root/"tests/test_acmp.cpp").read_text(); table=json.loads((root/"tests/mutations.json").read_text())
env=os.environ.copy();env.update(TSN_CLANG=os.environ.get("TSN_CLANG","clang-18"),PYTHONDONTWRITEBYTECODE="1")
log=P/"receipts/local/cache-controls";log.mkdir(exist_ok=True); rows=[]
def run(label,expected,h=header,s=source,t=tests,m=table):
 for path,value in [("include/acmp.h",h),("src/acmp.c",s),("tests/test_acmp.cpp",t),("tests/mutations.json",json.dumps(m))]: (work/path).write_text(value)
 r=subprocess.run([sys.executable,"-O","scripts/check_acmp_cache.py"],cwd=work,env=env,text=True,capture_output=True,timeout=60)
 (log/(label+".log")).write_text(r.stdout+r.stderr); (log/(label+".rc")).write_text(str(r.returncode)+"\n")
 row={"control":label,"rc":r.returncode,"expected":"accept" if expected else "reject","pass":(r.returncode==0)==expected};rows.append(row); print(json.dumps(row),flush=True)
run("head",True)
plants={field:next(m for m in table if m["name"]=="acmp-publish-reset-"+field+"-cache") for field in ("bound","started","stream")}
for field,plant in plants.items():
 run(field+"-missing-plant",False,m=[m for m in table if m is not plant])
 needle=plant["kills"][0]["needle"]
 run(field+"-missing-assertion",False,t=tests.replace(needle,"removed assertion control"))
 other=plants["stream" if field!="stream" else "bound"]
 shared=[dict(m,kills=copy.deepcopy(other["kills"])) if m is plant else m for m in table]
 run(field+"-shared-assertion",False,m=shared)
h=header.replace("struct acmp_sink {","struct acmp_sink {\n\tbool published_future;")
s=source.replace("\tmemset(s, 0, sizeof *s);","\tbool published_future = s->published_future;\n\tmemset(s, 0, sizeof *s);",1)
s=s.replace("\ts->published_bound = published_bound;","\ts->published_future = published_future;\n\ts->published_bound = published_bound;",1)
future={"name":"acmp-publish-reset-future-cache","path":"src/acmp.c","old":"\ts->published_future = published_future;\n","new":"\t(void)published_future;\n","kills":[{"test":"AcmpCore.FutureCachePreserved","needle":"future cache preservation independent assertion"}]}
t=tests+"\nnamespace acmp_test {\nTEST_F(AcmpCore, FutureCachePreserved) { a.sinks[0].published_future = true; acmp_restore_rollback(&a); EXPECT_TRUE(a.sinks[0].published_future) << \"future cache preservation independent assertion\"; }\n}\n"
# The gate reads compiler tokens and owned assertions; a future field cannot rely on existing coverage.
run("future-no-coverage",False,h=h,s=s)
run("future-no-assertion",False,h=h,s=s,m=table+[future])
run("future-no-plant",False,h=h,s=s,t=t)
run("future-shared-assertion",False,h=h,s=s,t=t,m=table+[dict(future,kills=copy.deepcopy(plants["bound"]["kills"]))])
run("future-own-coverage",True,h=h,s=s,t=t,m=table+[future])
# Restore the disposable input as well.
run("restored-control",True)
(P/"receipts/cache-controls.json").write_text(json.dumps(rows,indent=2)+"\n")
sys.exit(not all(x["pass"] for x in rows))
