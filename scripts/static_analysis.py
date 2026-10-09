#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Analyze every production source and the example. Warnings fail the gate."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
files = sorted(str(p.relative_to(ROOT)) for directory in ("src", "examples") for p in (ROOT / directory).rglob("*.c"))
commands = [["cppcheck", "--enable=warning,style,performance,portability", "--error-exitcode=1", "--std=c11", "--suppress=constParameterPointer:src/maap.c:262", "--suppress=constParameterCallback:examples/adp_port.c:32", "--suppress=constParameterCallback:examples/adp_port.c:40", "--suppress=constParameterCallback:examples/adp_port.c:46", "--suppress=redundantAssignment:examples/rv32/smoke.c:136", "-Iinclude", "-j16", *files]]
commands += [["clang-tidy", "--warnings-as-errors=*", "--checks=-*,clang-analyzer-*,bugprone-*,performance-*,-bugprone-signed-bitwise,-bugprone-easily-swappable-parameters,-clang-analyzer-security.insecureAPI.DeprecatedOrUnsafeBufferHandling", file, "--", "-std=c11", "-Iinclude", "-DNDEBUG"] for file in files]


def run(command):
    result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result.returncode, result.stdout

with ThreadPoolExecutor(max_workers=16) as pool:
    results = list(pool.map(run, commands))
for rc, output in results:
    print(output, end="")
raise SystemExit(any(rc != 0 for rc, _ in results))
