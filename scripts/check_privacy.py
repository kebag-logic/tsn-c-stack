#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Scan reachable commit metadata and blobs, then the current source tree."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
# Construct audit terms so the scanner does not flag its own pattern table.
WORDS = ["co" + "dex", "chat" + "gpt", "clau" + "de", "anth" + "ropic", "open" + "ai",
         "gem" + "ini", "cop" + "ilot", "gpt" + "-", "cursor" + " agent"]
PATTERNS = [re.compile(r"(?i)\b" + re.escape(word)) for word in WORDS]
PATTERNS += [re.compile(re.escape("/" + name + "/")) for name in ("home", "Users", "data", "tmp")]
PATTERNS += [re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")]
OWNER_SQUASH = "ae982af85ec97286bd35b39403926d8f0eaec81d"
IDENTITY = "hackerman-kl <hackerman-kl@kebag-logic.com>"
WEB_FLOW = ["hackerman-kl <161579364+Mister-M-alt@users.noreply.github.com>", "GitHub <noreply@github.com>"]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def identity_ok(lines):
    return lines[:2] in ([IDENTITY, IDENTITY], WEB_FLOW)


def selftest():
    cases = [([IDENTITY, IDENTITY], True), (WEB_FLOW, True), ([WEB_FLOW[0], IDENTITY], False),
             ([IDENTITY, WEB_FLOW[1]], False), (["someone <a@b.c>", WEB_FLOW[1]], False),
             (["someone <a@b.c>", "someone <a@b.c>"], False)]
    bad = [case for case, want in cases if identity_ok(case) != want]
    print("privacy selftest: " + ("fail " + repr(bad) if bad else f"{len(cases)} identity controls pass"))
    return bool(bad)


def scan(label, data):
    text = data.decode("utf-8", errors="replace")
    return [label + ": restricted content" for pattern in PATTERNS if pattern.search(text)]


def main():
    errors = []
    commits = git("rev-list", "HEAD").decode().splitlines()
    for commit in commits:
        data = git("show", "-s", "--format=%an <%ae>%n%cn <%ce>%n%B", commit)
        lines = data.decode().splitlines()
        if commit != OWNER_SQUASH and not identity_ok(lines):
            errors.append(commit + ": unexpected identity")
        if commit != OWNER_SQUASH and len([line for line in lines[2:] if line.strip()]) != 1:
            errors.append(commit + ": commit message must be one line")
        errors += scan(commit, data)
    if OWNER_SQUASH in commits:
        print("privacy: exact owner squash metadata exception; content scanning remains enabled")
    objects = git("rev-list", "--objects", "HEAD").decode().splitlines()
    unique = {line.split(" ", 1)[0] for line in objects}
    blobs = 0
    for oid in sorted(unique):
        if git("cat-file", "-t", oid).strip() != b"blob":
            continue
        blobs += 1
        errors += scan(oid, git("cat-file", "blob", oid))
    files = set(git("ls-files", "--cached", "--others", "--exclude-standard", "-z").decode().split("\0")) - {""}
    for name in sorted(files):
        path = ROOT / name
        if path.is_file():
            errors += scan(name, path.read_bytes())
    print("\n".join(errors) if errors else f"privacy: {len(commits)} commits, {blobs} historical blobs, {len(files)} current files; pass")
    return bool(errors)

if __name__ == "__main__":
    import sys
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
