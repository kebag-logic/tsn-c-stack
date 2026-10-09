#!/usr/bin/env python3
"""Plant faults in a disposable copy of scripts/check_privacy.py and record which controls catch them.
Usage: python3 -I mutant_probes.py <disposable-clone-at-exact-head>"""
import os, subprocess, sys
REPO = sys.argv[1]
HEAD = "61fb7c9a523b89cb96d493c5baf9f7f866ebed85"
GATE = os.path.join(REPO, "scripts", "check_privacy.py")
H, HE = "hackerman-kl", "hackerman-kl@kebag-logic.com"
NE = "161579364+Mister-M-alt@users.noreply.github.com"
G, GE = "GitHub", "noreply@github.com"
ORIG = open(GATE).read()
OK = "    return lines[:2] in ([IDENTITY, IDENTITY], WEB_FLOW)\n"
MUTANTS = {
    "none (control)": [],
    "accept-any-noreply-author-with-github-committer": [(OK, OK.rstrip("\n") + ' or (lines[1:2] == WEB_FLOW[1:] and lines[0].endswith("@users.noreply.github.com>"))\n')],
    "order-insensitive-pair": [(OK, "    return sorted(lines[:2]) in (sorted([IDENTITY, IDENTITY]), sorted(WEB_FLOW))\n")],
    "case-insensitive-pair": [(OK, "    return [l.lower() for l in lines[:2]] in ([IDENTITY.lower()] * 2, [w.lower() for w in WEB_FLOW])\n")],
    "webflow-checks-committer-only": [(OK, "    return lines[:2] == [IDENTITY, IDENTITY] or lines[1:2] == WEB_FLOW[1:]\n")],
    "webflow-checks-author-only": [(OK, "    return lines[:2] == [IDENTITY, IDENTITY] or lines[:1] == WEB_FLOW[:1]\n")],
    "accept-everything": [(OK, "    return True\n")],
    "main-keeps-old-holder-only-rule": [("not identity_ok(lines)", "lines[:2] != [IDENTITY, IDENTITY]")],
    "webflow-exempt-from-one-line-rule": [("if commit != OWNER_SQUASH and len(", "if commit != OWNER_SQUASH and lines[:2] != WEB_FLOW and len(")],
    "owner-squash-exception-widened-to-webflow": [("if commit != OWNER_SQUASH and len(", "if commit != OWNER_SQUASH and not (lines[:2] == WEB_FLOW and commit.startswith(\"\")) and len(")],
}
SYNTH = {  # name: (author, committer, message, expect_refused)
    "foreign-noreply": ((H, "99999999+someone-else@users.noreply.github.com"), (G, GE), "Subject\n"),
    "reversed": ((G, GE), (H, NE), "Subject\n"),
    "case-variant": ((H, NE.lower()), (G, GE), "Subject\n"),
    "holder+github": ((H, HE), (G, GE), "Subject\n"),
    "webflow-multiline": ((H, NE), (G, GE), "Subject\n\n* a\n"),
}
def git(*a, env=None, inp=None):
    return subprocess.run(["git", *a], cwd=REPO, env=env, input=inp, capture_output=True, text=True, check=True).stdout.strip()
def run(*a):
    return subprocess.run([sys.executable, "-I", GATE, *a], cwd=REPO, capture_output=True, text=True).returncode
git("checkout", "-q", "--detach", HEAD)
tree = git("rev-parse", "HEAD^{tree}")
commits = {}
for name, (a, c, msg) in SYNTH.items():
    env = dict(os.environ, GIT_AUTHOR_NAME=a[0], GIT_AUTHOR_EMAIL=a[1], GIT_COMMITTER_NAME=c[0], GIT_COMMITTER_EMAIL=c[1])
    commits[name] = git("commit-tree", tree, "-p", HEAD, env=env, inp=msg)
print("mutant\tselftest_rc\tpublished_history_rc\t" + "\t".join(SYNTH) + "\tcaught_by_selftest\tcaught_by_any")
for name, edits in MUTANTS.items():
    text = ORIG
    for old, new in edits:
        assert text.count(old) == 1, (name, old)
        text = text.replace(old, new)
    open(GATE, "w").write(text)
    st = run("--selftest")
    pub = run()
    synth = []
    for cname, sha in commits.items():
        git("checkout", "-q", "--detach", sha)
        synth.append(run())
        git("checkout", "-q", "--detach", HEAD)
    any_caught = st != 0 or pub != 0 or any(r == 0 for r in synth)
    print(f"{name}\t{st}\t{pub}\t" + "\t".join(str(r) for r in synth) + f"\t{'yes' if st else 'NO'}\t" + ("yes" if st or pub else "NO (synthetic only)" if any(r == 0 for r in synth) else "NO"))
open(GATE, "w").write(ORIG)
print("restored:", git("status", "--porcelain") == "" and git("rev-parse", "HEAD") == HEAD)
