#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Kebag Logic
# SPDX-License-Identifier: MIT
"""Run each core defect in isolation. Only named assertion failures count."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import xml.etree.ElementTree as ET
from test_registry import environment, registered
from needle_audit import validate_needles

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {"port": "test_port.cpp", "adp": "test_adp.cpp", "acmp": "test_acmp.cpp", "maap": "test_maap.cpp",
           "adp_debug": "test_adp_reentry.cpp", "adp_release": "test_adp_reentry.cpp", "maap_debug": "test_maap_debug.cpp"}
HEADER_SLOTS = threading.Semaphore(3)


def run(cmd, log, **kwargs):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, timeout=120, **kwargs)
    log.append(result.stdout)
    return result.returncode


def cflags(arm):
    return ["-std=c11", "-O0", "-g", "-Wall", "-Wextra", "-Werror"] + (
        [] if arm.endswith("_debug") else ["-DNDEBUG", "-DCTRL_REENTRY_ASSERT"])


def cppflags(arm):
    return ["-std=c++20", "-O0", "-g", "-Wall", "-Wextra", "-Werror"] + (
        ["-DADP_TEST_RELEASE"] if arm == "adp_release" else [])


def execute(binary, xml, log, filters=None):
    # A reused work directory must never supply evidence for this execution.
    xml.unlink(missing_ok=True)
    patterns = [k['test'] + ('*' if k['test'].endswith('/') else '') for k in (filters or [])]
    expected = set(registered(binary, patterns))
    env = environment()
    command = [str(binary), "--gtest_output=xml:" + str(xml)]
    if filters:
        command.append("--gtest_filter=" + ":".join(k["test"] + ("*" if k["test"].endswith("/") else "") for k in filters))
    rc = run(command, log, env=env)
    try:
        doc = ET.parse(xml).getroot()
        cases = list(doc.iter('testcase'))
        names = [case.attrib['classname'] + '.' + case.attrib['name'] for case in cases]
        complete = (doc.tag == 'testsuites' and len(cases) == int(doc.attrib['tests'])
                    and len(names) == len(set(names)) and set(names) == expected
                    and int(doc.attrib['errors']) == 0
                    and int(doc.attrib['disabled']) == 0
                    and int(doc.attrib['failures']) == sum(bool(c.findall('failure')) for c in cases)
                    and all(c.get('status') == 'run' and c.get('result') == 'completed'
                            and not c.findall('skipped') and not c.findall('error') for c in cases))
        if not complete:
            raise ValueError('incomplete report or registration mismatch')
    except (OSError, ET.ParseError, KeyError, ValueError) as error:
        log.append('Report refused: ' + str(error) + '\n')
        return rc, {}, 0
    failures = {}
    for case in doc.iter("testcase"):
        messages = [e.get("message", "") for e in case.findall("failure")]
        if messages:
            failures[case.get("classname") + "." + case.get("name")] = "\n".join(messages)
    return rc, failures, int(doc.get("tests", "0"))


def matches(kill, failures):
    return any((name.startswith(kill['test']) if kill['test'].endswith('/') else name == kill['test'])
               and kill["needle"] in message
               for name, message in failures.items())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=16)
    parser.add_argument("--select", default="")
    parser.add_argument("--discover", action="store_true", help="Report candidate killers; never grade as a pass")
    args = parser.parse_args()
    mutants = json.loads((ROOT / "tests/mutations.json").read_text())
    errors = validate_needles(mutants)
    if errors:
        raise SystemExit('\n'.join(errors))
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    baseline = work / "baseline"
    baseline.mkdir(exist_ok=True)
    cc = os.environ.get("CC", "gcc")
    cxx = os.environ.get("CXX", "g++")
    log = []
    assert run([cxx, *cppflags(""), "-c", str(ROOT / "tests/main.cpp"), "-o", str(baseline / "main.o")], log) == 0
    assert run([cc, *cflags("port"), "-I" + str(ROOT / "include"), "-c", str(ROOT / "examples/adp_port.c"), "-o", str(baseline / "port_extra.o")], log) == 0
    def extra(arm):
        return [str(baseline / "port_extra.o")] if arm == "port" else []
    def prepare(arm):
        module = "adp" if arm == "port" else arm.split("_")[0]
        local = []
        commands = [
            [cc, *cflags(arm), "-I" + str(ROOT / "include"), "-c", str(ROOT / f"src/{module}.c"), "-o", str(baseline / (arm + ".c.o"))],
            [cxx, *cppflags(arm), "-I" + str(ROOT / "include"), "-I" + str(ROOT / "examples"), "-c", str(ROOT / "tests" / SOURCES[arm]), "-o", str(baseline / (arm + ".cpp.o"))],
            [cxx, str(baseline / (arm + ".c.o")), str(baseline / (arm + ".cpp.o")), str(baseline / "main.o"), *extra(arm), "-lgmock", "-lgtest", "-pthread", "-o", str(baseline / arm)]]
        for cmd in commands:
            if run(cmd, local) != 0:
                raise RuntimeError("baseline build failed: " + "".join(local))
        rc, failures, count = execute(baseline / arm, baseline / (arm + ".xml"), local)
        (baseline / (arm + ".log")).write_text("".join(local))
        if rc != 0 or failures or count == 0:
            raise RuntimeError("baseline test failed: " + arm)
    with ThreadPoolExecutor(max_workers=min(args.jobs, 5)) as pool:
        list(pool.map(prepare, SOURCES))
    names = [m["name"] for m in mutants]
    if len(set(names)) != len(names):
        raise RuntimeError("duplicate mutant name")
    selected = [m for m in mutants if args.select in m["name"]]
    if not selected:
        raise RuntimeError("empty campaign")
    def plant(m):
        directory = work / m["name"]
        directory.mkdir(exist_ok=True)
        local = []
        result = {"name": m["name"], "status": "ERROR"}
        try:
            for name in ("src", "include"):
                shutil.copytree(ROOT / name, directory / name, dirs_exist_ok=True)
            target = directory / m["path"]
            source = target.read_text()
            if source.count(m["old"]) != 1:
                raise RuntimeError("plant must match exactly once")
            target.write_text(source.replace(m["old"], m["new"]))
            module = target.stem
            default_arm = "maap_debug" if any(k["test"].startswith("MaapDebug.") for k in m["kills"]) else module
            arms = sorted({k.get("arm", default_arm) for k in m["kills"]} or {default_arm})
            all_caught = bool(m["kills"])
            failures_all = {}
            for arm in arms:
                kills = [k for k in m["kills"] if k.get("arm", default_arm) == arm]
                obj = directory / (arm + ".o")
                rc = run([cc, *cflags(arm), "-I" + str(directory / "include"), "-c", str(directory / f"src/{module}.c"), "-o", str(obj)], local)
                if rc != 0:
                    raise RuntimeError("mutant build failed")
                test_obj = baseline / (arm + ".cpp.o")
                if target.suffix == ".h":
                    test_obj = directory / (arm + ".test.o")
                    with HEADER_SLOTS:
                        rc = run([cxx, *cppflags(arm), "-I" + str(directory / "include"), "-I" + str(ROOT / "tests"), "-I" + str(ROOT / "examples"), "-c", str(ROOT / "tests" / SOURCES[arm]), "-o", str(test_obj)], local)
                    if rc != 0:
                        raise RuntimeError("mutated header test build failed")
                binary = directory / arm
                rc = run([cxx, str(obj), str(test_obj), str(baseline / "main.o"), *extra(arm), "-lgmock", "-lgtest", "-pthread", "-o", str(binary)], local)
                if rc != 0:
                    raise RuntimeError("mutant link failed")
                rc, failures, count = execute(binary, directory / (arm + ".xml"), local, kills)
                failures_all.update(failures)
                all_caught = all_caught and rc == 1 and count > 0 and all(matches(k, failures) for k in kills)
            result.update(rc=rc, failures=failures_all, tests=count)
            result["status"] = "CAUGHT" if all_caught else "ESCAPED"
        except (RuntimeError, subprocess.TimeoutExpired) as error:
            result["error"] = str(error)
        (directory / "run.log").write_text("".join(local))
        print(result["status"], m["name"], flush=True)
        return result
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        results = list(pool.map(plant, selected))
    (work / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    counts = {status: sum(r["status"] == status for r in results) for status in ("CAUGHT", "ESCAPED", "ERROR")}
    print(json.dumps(counts))
    return int(args.discover or counts["ESCAPED"] != 0 or counts["ERROR"] != 0)

if __name__ == "__main__":
    raise SystemExit(main())
