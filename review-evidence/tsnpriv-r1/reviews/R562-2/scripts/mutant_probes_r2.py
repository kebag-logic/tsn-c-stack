#!/usr/bin/env python3
"""Plant faults in a disposable copy of scripts/check_privacy.py at a given head and record
which controls catch them: the --selftest, the real-history gate, and synthetic commits.
The first ten mutants are R562-1's set (edit strings unchanged); the rest are new in round 2.
Usage: python3 -I mutant_probes_r2.py <disposable-clone> <exact-head>"""
import os, subprocess, sys
REPO, HEAD = sys.argv[1], sys.argv[2]
GATE = os.path.join(REPO, "scripts", "check_privacy.py")
H, HE = "hackerman-kl", "hackerman-kl@kebag-logic.com"
NE = "161579364+Mister-M-alt@users.noreply.github.com"
G, GE = "GitHub", "noreply@github.com"
OK = "    return lines[:2] in ([IDENTITY, IDENTITY], WEB_FLOW)\n"
ONE = "if commit != OWNER_SQUASH and len("
MUTANTS = {
    "none (control)": [],
    # R562-1 set
    "accept-any-noreply-author-with-github-committer": [(OK, OK.rstrip("\n") + ' or (lines[1:2] == WEB_FLOW[1:] and lines[0].endswith("@users.noreply.github.com>"))\n')],
    "order-insensitive-pair": [(OK, "    return sorted(lines[:2]) in (sorted([IDENTITY, IDENTITY]), sorted(WEB_FLOW))\n")],
    "case-insensitive-pair": [(OK, "    return [l.lower() for l in lines[:2]] in ([IDENTITY.lower()] * 2, [w.lower() for w in WEB_FLOW])\n")],
    "webflow-checks-committer-only": [(OK, "    return lines[:2] == [IDENTITY, IDENTITY] or lines[1:2] == WEB_FLOW[1:]\n")],
    "webflow-checks-author-only": [(OK, "    return lines[:2] == [IDENTITY, IDENTITY] or lines[:1] == WEB_FLOW[:1]\n")],
    "accept-everything": [(OK, "    return True\n")],
    "main-keeps-old-holder-only-rule": [("not identity_ok(lines)", "lines[:2] != [IDENTITY, IDENTITY]")],
    "webflow-exempt-from-one-line-rule": [(ONE, "if commit != OWNER_SQUASH and lines[:2] != WEB_FLOW and len(")],
    "owner-squash-exception-widened-to-webflow": [(ONE, "if commit != OWNER_SQUASH and not (lines[:2] == WEB_FLOW and commit.startswith(\"\")) and len(")],
    # round-2 additions
    "holder-exempt-from-one-line-rule": [(ONE, "if commit != OWNER_SQUASH and lines[:2] != [IDENTITY, IDENTITY] and len(")],
    "one-line-rule-dropped": [(ONE, "if False and len(")],
    "owner-exception-by-prefix": [("    if commit != OWNER_SQUASH and not identity_ok", "    if not commit.startswith(OWNER_SQUASH[:1]) and not identity_ok")],
    "owner-exception-dropped": [("    if commit != OWNER_SQUASH and not identity_ok", "    if not identity_ok")],
    "selftest-always-passes": [("    return bool(bad)\n", "    return False\n")],
    "main-skips-commit-errors": [("        errors += commit_errors(commit, lines)\n", "        errors += []\n")],
    "main-uses-identity-only": [("        errors += commit_errors(commit, lines)\n", "        errors += [] if identity_ok(lines) else [commit]\n")],
    "unknown-args-run-main": [("    if sys.argv[1:] not in ([], [\"--selftest\"]):\n", "    if False:\n")],
    "accept-empty-message": [(") != 1:\n", ") > 1:\n")],
}
SYNTH = {  # name: (author, committer, message) - every one must be refused
    "foreign-noreply": ((H, "99999999+someone-else@users.noreply.github.com"), (G, GE), "Subject\n"),
    "reversed": ((G, GE), (H, NE), "Subject\n"),
    "case-variant": ((H, NE.lower()), (G, GE), "Subject\n"),
    "holder+github": ((H, HE), (G, GE), "Subject\n"),
    "webflow-multiline": ((H, NE), (G, GE), "Subject\n\n* a\n"),
    "holder-multiline": ((H, HE), (H, HE), "Subject\n\nBody\n"),
    "foreign-pair": (("someone", "a@b.c"), ("someone", "a@b.c"), "Subject\n"),
}
def git(*a, env=None, inp=None):
    return subprocess.run(["git", *a], cwd=REPO, env=env, input=inp, capture_output=True, text=True, check=True).stdout.strip()
def run(*a):
    return subprocess.run([sys.executable, "-I", GATE, *a], cwd=REPO, capture_output=True, text=True).returncode
git("checkout", "-q", "--detach", HEAD)
assert git("rev-parse", "HEAD") == HEAD and git("status", "--porcelain") == ""
ORIG = open(GATE).read()
tree = git("rev-parse", "HEAD^{tree}")
commits = {}
for name, (a, c, msg) in SYNTH.items():
    env = dict(os.environ, GIT_AUTHOR_NAME=a[0], GIT_AUTHOR_EMAIL=a[1], GIT_COMMITTER_NAME=c[0], GIT_COMMITTER_EMAIL=c[1])
    commits[name] = git("commit-tree", tree, "-p", HEAD, env=env, inp=msg)
print("mutant\tselftest_rc\tbadarg_rc\tpublished_history_rc\t" + "\t".join(SYNTH) + "\tcaught_by_selftest\tcaught_by_any")
for name, edits in MUTANTS.items():
    text = ORIG
    for old, new in edits:
        assert text.count(old) == 1, (name, old)
        text = text.replace(old, new)
    with open(GATE, "w") as f:
        f.write(text)
    st = run("--selftest")
    badarg = run("--selftst")
    pub = run()
    synth = []
    for cname, sha in commits.items():
        git("checkout", "-q", "--detach", sha)
        synth.append(run())
        git("checkout", "-q", "--detach", HEAD)
    caught_any = st != 0 or pub != 0 or badarg == 0 or any(r == 0 for r in synth)
    print(f"{name}\t{st}\t{badarg}\t{pub}\t" + "\t".join(str(r) for r in synth)
          + f"\t{'yes' if st else 'NO'}\t{'yes' if caught_any else 'NO'}")
with open(GATE, "w") as f:
    f.write(ORIG)
print("restored:", git("status", "--porcelain") == "" and git("rev-parse", "HEAD") == HEAD)
