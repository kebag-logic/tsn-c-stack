#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Require MIT identifiers on repository sources, scripts and build files."""
import argparse
from pathlib import Path
import subprocess
import re

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {".c", ".h", ".cpp", ".hpp", ".py", ".yml", ".yaml", ".cmake", ".S", ".ld"}


def valid(text):
    lines = [line for line in text.splitlines() if re.match(r"\s*(?://|#|/\*)\s*SPDX-License-Identifier:", line)]
    return bool(lines) and all(line.split("SPDX-License-Identifier:", 1)[1].removesuffix('*/').strip() == "MIT" for line in lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        if not (valid("// SPDX-License-Identifier: MIT\n")):
            raise RuntimeError('validation failed: valid("// SPDX-License-Identifier: MIT\\n")')
        if not (valid("/* SPDX-License-Identifier: MIT */\n")):
            raise RuntimeError('validation failed: valid("/* SPDX-License-Identifier: MIT */\\n")')
        if valid("// SPDX-License-Identifier: Apache-2.0\n"):
            raise RuntimeError('validation failed: not valid("// SPDX-License-Identifier: Apache-2.0\\n")')
        if valid("int n;\n"):
            raise RuntimeError('validation failed: not valid("int n;\\n")')
        if valid("// SPDX-License-Identifier: MIT\n// SPDX-License-Identifier: GPL-2.0\n"):
            raise RuntimeError('validation failed: not valid("// SPDX-License-Identifier: MIT\\n// SPDX-License-Identifier: GPL-2.0\\n")')
        print("license: valid control passes; three bad controls refused")
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    bad = []
    for name in set(names) - {""}:
        file = ROOT / name
        if (file.suffix in EXTENSIONS or file.name == "CMakeLists.txt") and not valid(file.read_text()):
            bad.append(name)
    if "Kebag Logic" not in (ROOT / "LICENSE").read_text():
        bad.append("LICENSE holder")
    print("\n".join(sorted(bad)) if bad else "license: pass")
    return bool(bad)

if __name__ == "__main__":
    raise SystemExit(main())
