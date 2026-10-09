#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Reviewer mutation probe: plant each variant in a disposable copy, build and run adp_tests.
Usage: mutants.py <clone> <workdir> <jobs>"""
import concurrent.futures as cf, json, os, shutil, subprocess, sys
from pathlib import Path

clone, work, jobs = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
V = "\t    (frame[ADP_HEADER_BYTES + 1u] & 0x70u) != 0u ||\n"
C = "\t    (wire_be16(frame + ADP_HEADER_BYTES + 2u) & 0x07FFu) != ADP_CONTROL_DATA_LENGTH ||\n"
TGT = "\tif (!a->enabled || a->state != ADP_STATE_WAITING) {"
MUTANTS = {
    "control-unmutated": [],
    "version-mask-only-bit4": [(V, V.replace("0x70u", "0x10u"))],
    "version-mask-includes-sv": [(V, V.replace("0x70u", "0xF0u"))],
    "length-bound-81": [("len < ADP_FRAME_BYTES ||", "len < ADP_FRAME_BYTES - 1u ||")],
    "length-bound-over-strict": [("len < ADP_FRAME_BYTES ||", "len <= ADP_FRAME_BYTES ||")],
    "cdl-mask-dropped-full-word": [(C, C.replace(" & 0x07FFu", ""))],
    "cdl-mask-10-bit": [(C, C.replace("0x07FFu", "0x03FFu"))],
    "cdl-checked-only-nonzero": [(C, C.replace("!= ADP_CONTROL_DATA_LENGTH", "== 0u"))],
    "malformed-not-counted": [(V + C, ""), (TGT, "\tif ((frame[ADP_HEADER_BYTES + 1u] & 0x70u) != 0u || (wire_be16(frame + ADP_HEADER_BYTES + 2u) & 0x07FFu) != ADP_CONTROL_DATA_LENGTH) {\n\t\treturn;\n\t}\n" + TGT)],
    "checks-only-in-waiting": [(V + C, ""), (TGT, TGT[:-3] + "\n\t    || (frame[ADP_HEADER_BYTES + 1u] & 0x70u) != 0u || (wire_be16(frame + ADP_HEADER_BYTES + 2u) & 0x07FFu) != ADP_CONTROL_DATA_LENGTH) {\n\t\tif (a->enabled && a->state == ADP_STATE_WAITING) a->discarded++;")],
}

def run(name):
    tree = work / name
    shutil.rmtree(tree, ignore_errors=True)
    shutil.copytree(clone, tree / "src-tree", ignore=shutil.ignore_patterns(".git", "build*", "__pycache__"))
    src = tree / "src-tree/src/adp.c"
    text = src.read_text()
    for old, new in MUTANTS[name]:
        if text.count(old) != 1:
            return name, {"status": "PLANT-ERROR", "detail": old}
        text = text.replace(old, new)
    src.write_text(text)
    b = tree / "build"
    log = []
    for argv in (["cmake", "-S", str(tree / "src-tree"), "-B", str(b), "-DCMAKE_BUILD_TYPE=Debug", "-DTSN_SANITIZERS=ON",
                  "-DCMAKE_C_COMPILER=gcc", "-DCMAKE_CXX_COMPILER=g++"],
                 ["cmake", "--build", str(b), "--target", "adp_tests", "-j4"]):
        r = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        log.append(r.stdout)
        if r.returncode:
            (tree / "build.log").write_text("\n".join(log))
            return name, {"status": "BUILD-FAIL"}
    xml = tree / "adp.xml"
    r = subprocess.run([str(b / "adp_tests"), "--gtest_output=xml:" + str(xml)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    (tree / "run.log").write_text(r.stdout)
    import xml.etree.ElementTree as ET
    failed = sorted({(c.get("classname") + "." + c.get("name")) for c in ET.parse(xml).iter("testcase") if c.find("failure") is not None}) if xml.exists() else ["NO-XML"]
    return name, {"rc": r.returncode, "status": "KILLED" if r.returncode else "SURVIVED", "failed_tests": failed}

with cf.ThreadPoolExecutor(jobs) as ex:
    results = dict(ex.map(run, MUTANTS))
print(json.dumps(results, indent=1))
