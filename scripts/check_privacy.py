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


def commit_errors(commit, lines):
    errors = []
    if commit != OWNER_SQUASH and not identity_ok(lines):
        errors.append(commit + ": unexpected identity")
    if commit != OWNER_SQUASH and len([line for line in lines[2:] if line.strip()]) != 1:
        errors.append(commit + ": commit message must be one line")
    return errors


def selftest():
    other = "hackerman-kl <99999999+someone@users.noreply.github.com>"
    cases = [
        ("holder", [IDENTITY, IDENTITY, "Subject"], True),
        ("web-flow", WEB_FLOW + ["Subject (#1)"], True),
        ("owner-squash", ["x <x@y.z>", "x <x@y.z>", "Subject", "", "Body"], True),
        ("noreply-author-holder-committer", [WEB_FLOW[0], IDENTITY, "Subject"], False),
        ("holder-author-github-committer", [IDENTITY, WEB_FLOW[1], "Subject"], False),
        ("other-noreply-account", [other, WEB_FLOW[1], "Subject"], False),
        ("reversed-web-flow", [WEB_FLOW[1], WEB_FLOW[0], "Subject"], False),
        ("case-variant", [WEB_FLOW[0].lower(), WEB_FLOW[1], "Subject"], False),
        ("web-flow-two-lines", WEB_FLOW + ["Subject", "", "Body"], False),
        ("holder-two-lines", [IDENTITY, IDENTITY, "Subject", "", "Body"], False),
        ("foreign", ["someone <a@b.c>", "someone <a@b.c>", "Subject"], False),
    ]
    bad = []
    for name, lines, want in cases:
        commit = OWNER_SQUASH if name == "owner-squash" else "0" * 40
        if (not commit_errors(commit, lines)) != want:
            bad.append(name)
    print("privacy selftest: " + ("fail " + ", ".join(bad) if bad else f"{len(cases)} commit controls pass"))
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
        errors += commit_errors(commit, lines)
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
    if sys.argv[1:] not in ([], ["--selftest"]):
        raise SystemExit("usage: check_privacy.py [--selftest]")
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
