#!/usr/bin/env python3
"""Independently test individual publication-cache restore omissions.
Usage: cache_probes.py REPO PACKET. Run run_checks.py first for stock test objects.
"""
import pathlib,subprocess,sys,os,json,shlex,xml.etree.ElementTree as ET
repo,packet=map(lambda s:pathlib.Path(s).resolve(),sys.argv[1:3]);work=packet/"scratch/cache-probes";work.mkdir(exist_ok=True)
out=packet/"receipts/cache-probes";out.mkdir(parents=True,exist_ok=True)
env=os.environ.copy();env.pop("GTEST_FILTER",None)
def command(name,argv,expect=0):
 r=subprocess.run(list(map(str,argv)),env=env,cwd=work,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
 (out/(name+".log")).write_bytes(r.stdout);(out/(name+".rc")).write_text(str(r.returncode)+"\n")
 if expect is not None:assert r.returncode==expect,(name,r.returncode)
 return r.returncode
flags=shlex.split(subprocess.check_output(["pkg-config","--cflags","gtest","gmock"],text=True)); libs=shlex.split(subprocess.check_output(["pkg-config","--libs","gmock","gtest"],text=True))
witness=r"""
// REQ: ACMP-10
TEST_F(AcmpCore, ReviewerCacheStartedStopOnRestore) {
    bind(0);
    ASSERT_TRUE(a.sinks[0].published_started);
    const auto stopped = payload(kRecValid, 1u, kTkA, kCtl1);
    fk.clear();
    ASSERT_EQ(acmp_restore_binding(&a, 0, stopped.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    ASSERT_TRUE(fk.pubs.empty());
    acmp_open(&a);
    ASSERT_EQ(fk.pubs.size(), 1u) << "cache started stop is published at open";
    EXPECT_TRUE(fk.pubs[0].bound && !fk.pubs[0].started && !fk.pubs[0].moved);
}
// REQ: ACMP-10
TEST_F(AcmpCore, ReviewerCacheBoundStoppedWithdrawal) {
    bind(0, kTkA, 1, kCtl1, true);
    ASSERT_TRUE(a.sinks[0].published_bound && !a.sinks[0].published_started);
    const auto none = payload(0u, 0u, 0u, 0u);
    fk.clear();
    ASSERT_EQ(acmp_restore_binding(&a, 0, none.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    ASSERT_TRUE(fk.pubs.empty());
    acmp_open(&a);
    ASSERT_EQ(fk.pubs.size(), 1u) << "cache bound stopped withdrawal is published at open";
    EXPECT_TRUE(!fk.pubs[0].bound && !fk.pubs[0].started && !fk.pubs[0].moved);
}
// REQ: ACMP-10
TEST_F(AcmpCore, ReviewerCacheStreamWithdrawal) {
    to_state(0, ACMP_SETTLED_NO_RSV);
    const auto none = payload(0u, 0u, 0u, 0u);
    fk.clear();
    ASSERT_EQ(acmp_restore_binding(&a, 0, none.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    acmp_open(&a);
    ASSERT_EQ(fk.pubs.size(), 1u);
    EXPECT_TRUE(fk.pubs[0].stream == 0u && fk.pubs[0].moved) << "cache stream withdrawal reports movement";
}
"""
text=(repo/"tests/test_acmp.cpp").read_text();idx=text.rfind("}");(work/"witness.cpp").write_text(text[:idx]+witness+text[idx:])
command("witness-build",["g++","-std=c++20","-O0","-g","-Wall","-Wextra","-Werror",*flags,"-I"+str(repo/"include"),"-I"+str(repo/"tests"),"-c",work/"witness.cpp","-o",work/"witness.o"])
base=packet/"scratch/mutations/baseline";source=(repo/"src/acmp.c").read_text();summary=[]
for field in ["head","bound","started","stream"]:
 modified=source
 if field!="head":
  old=f"\ts->published_{field} = published_{field};";assert source.count(old)==1
  modified=source.replace(old,f"\t(void)published_{field};")
 (work/(field+".c")).write_text(modified)
 command(field+"-compile",["gcc","-std=c11","-O0","-g","-Wall","-Wextra","-Werror","-DNDEBUG","-DCTRL_REENTRY_ASSERT","-I"+str(repo/"include"),"-c",work/(field+".c"),"-o",work/(field+".o")])
 for kind,obj in [("stock",base/"acmp.cpp.o"),("witness",work/"witness.o")]:
  name=field+"-"+kind;binary=work/name;xml=out/(name+".xml")
  command(name+"-link",["g++",work/(field+".o"),obj,base/"main.o",*libs,"-o",binary])
  rc=command(name,[binary,"--gtest_output=xml:"+str(xml)],None)
  root=ET.parse(xml).getroot();fail=[c.get("name") for c in root.iter("testcase") if c.find("failure") is not None]
  row={"plant":field,"suite":kind,"rc":rc,"tests":int(root.get("tests")),"failures":fail};summary.append(row);print(json.dumps(row),flush=True)
  assert int(root.get("errors"))==0 and int(root.get("disabled"))==0
  assert rc in [0,1]
(out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
assert all(r["rc"]==0 for r in summary if r["plant"]=="head")
assert all(r["rc"]==1 for r in summary if r["plant"]!="head" and r["suite"]=="witness")
