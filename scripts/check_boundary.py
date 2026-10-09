#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Refuse foreign includes and dynamic allocation in the portable library."""
import argparse
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
C_HEADERS = set("assert complex ctype errno fenv float inttypes iso646 limits locale math setjmp signal stdalign stdarg stdatomic stdbool stddef stdint stdio stdlib stdnoreturn string tgmath threads time uchar wchar wctype".split())
# Hosted concurrency and clock APIs belong in ports, even when standardized.
C_HEADERS -= {"threads", "time", "signal", "setjmp"}


def check(root):
    errors = []
    headers = {p.name for p in (root / "include").glob("*.h")}
    for directory in ("src", "include"):
        for path in sorted((root / directory).rglob("*")):
            if not path.is_file():
                continue
            raw = path.read_text().replace("\\\n", "")
            code = re.sub(r"/\*.*?\*/|//[^\n]*", "", raw, flags=re.S)
            for line in code.splitlines():
                if re.match(r"\s*#\s*(include|include_next|import)\b", line):
                    match = re.fullmatch(r"\s*#\s*include\s+([<\"])([^>\"]+)[>\"]\s*", line)
                    allowed = match and ((match[1] == "<" and match[2].endswith(".h") and match[2][:-2] in C_HEADERS) or
                                         (match[1] == chr(34) and match[2] in headers))
                    if not allowed:
                        errors.append(f"{path.relative_to(root)}: forbidden include: {line.strip()}")
            if re.search(r"\b(malloc|calloc|realloc|free|aligned_alloc)\s*\(", code):
                errors.append(f"{path.relative_to(root)}: dynamic allocation")
    return errors


def selftest():
    with tempfile.TemporaryDirectory(prefix="boundary-") as directory:
        root = Path(directory)
        (root / "src").mkdir()
        (root / "include").mkdir()
        (root / "include/own.h").write_text("")
        file = root / "src/control.c"
        file.write_text("#include <stdint.h>\n#include \"own.h\"\n")
        assert not check(root)
        for plant in ("#include \"mbx.h\"", "#include <unistd.h>", "#include \"../outside.h\"",
                      "#include FOREIGN", "#include_next <stdint.h>", "#inc\\\nlude <unistd.h>",
                      "void f(void) { malloc(2); }"):
            file.write_text(plant)
            assert check(root), plant
    print("boundary: valid control passes; seven forbidden controls refused")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
    errors = check(ROOT)
    print("\n".join(errors) if errors else "boundary: pass")
    raise SystemExit(bool(errors))
