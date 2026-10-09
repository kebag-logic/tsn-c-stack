#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Export the fixed import baseline into a new disposable clone."""
import argparse
import json
from pathlib import Path
import subprocess

REVISION = "6aa25dec977c6ad78bf4ff6275de47fb81d0c246"
PATHS = {}
for module in ("adp", "acmp", "maap"):
    for ext, directory in (("c", "src"), ("h", "include")):
        PATHS[f"sw/firmware/ctrl/{module}/{module}.{ext}"] = f"{directory}/{module}.{ext}"
PATHS["sw/firmware/ctrl/wire/wire.h"] = "include/wire.h"
for name in ("test_adp.cpp", "test_adp_reentry.cpp", "test_acmp.cpp", "acmp_fake.hpp", "test_maap.cpp", "test_maap_debug.cpp"):
    PATHS["sw/firmware/ctrl/test/" + name] = "tests/" + name
CALLBACK = '\nimport re\ncontents = value.get_contents_by_identifier(blob_id)\nif filename == b"tests/test_adp.cpp":\n    if b"TEST(AdpCore," not in contents:\n        return (None, mode, blob_id)\n    prefix = contents[:contents.index(b"// ---- the adapter")]\n    suffix = contents[contents.index(b"TEST(AdpCore,"):contents.index(b"TEST(AdpAdapter,")]\n    contents = prefix + suffix + b"\\n} // namespace\\n"\n    contents = re.sub(rb"// test_adp.cpp.*?(?=#include)", b"// ADP core cases over fake ports.\\n\\n", contents, flags=re.S)\nif filename == b"tests/test_maap.cpp":\n    if b"struct CsrRig" in contents:\n        contents = contents[:contents.index(b"struct CsrRig")] + b"\\n} // namespace\\n"\nfor header in (b"adp_mbx.h", b"ctrl_app.h", b"mbx_model.h", b"mbx_wire.h", b"maap_csr.h", b"fw_gtest.hpp"):\n    contents = contents.replace(b\'#include "\' + header + b\'"\\n\', b"")\ncontents = re.sub(rb"^FW_TALLY_LABEL.*?\\n", b"", contents, flags=re.M)\nif filename == b"tests/test_adp_reentry.cpp":\n    contents = re.sub(rb"namespace fw_test \\{.*?\\n\\}\\n\\}", b"", contents, flags=re.S)\ncontents = contents.replace(b"SPDX-License-Identifier: CERN-OHL-W-2.0", b"SPDX-License-Identifier: MIT")\nblob_id = value.insert_file_with_contents(contents)\nreturn (filename, mode, blob_id)\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--filter-program", default="git-filter-repo")
    args = parser.parse_args()
    source, destination = args.source.resolve(), args.destination.resolve()
    if destination.exists():
        raise SystemExit("destination must not exist")
    subprocess.run(["git", "clone", "--shared", "--no-checkout", str(source), str(destination)], check=True)
    subprocess.run(["git", "checkout", "--detach", REVISION], cwd=destination, check=True)
    command = [args.filter_program, "--force", "--refs", "HEAD"]
    for old, new in PATHS.items():
        command += ["--path", old, "--path-rename", old + ":" + new]
    command += ["--file-info-callback", CALLBACK, "--commit-callback",
                "commit.author_name = commit.committer_name = b'hackerman-kl'\n"
                "commit.author_email = commit.committer_email = b'hackerman-kl@kebag-logic.com'\n"
                "commit.message = b'Update portable protocol cores and tests\\n'"]
    subprocess.run(command, cwd=destination, check=True)
    print(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=destination, text=True).strip())

if __name__ == "__main__":
    main()
