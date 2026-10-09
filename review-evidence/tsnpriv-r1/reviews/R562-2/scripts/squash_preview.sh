#!/bin/sh
# Model the squash commit GitHub would create for PR #17 under the current repository settings
# (PR_TITLE subject, BLANK body, web-flow pair) on main's base, then run the gate on it.
# Usage: squash_preview.sh <disposable-clone> <head> <base> "<pr-title>" <pr-number>
set -u
W=$1; HEAD=$2; BASE=$3; TITLE=$4; NUM=$5
cd "$W" || exit 2
tree=$(git rev-parse "$HEAD^{tree}")
c=$(printf '%s (#%s)\n' "$TITLE" "$NUM" | env GIT_AUTHOR_NAME=hackerman-kl GIT_AUTHOR_EMAIL=161579364+Mister-M-alt@users.noreply.github.com GIT_COMMITTER_NAME=GitHub GIT_COMMITTER_EMAIL=noreply@github.com git commit-tree "$tree" -p "$BASE")
git checkout -q --detach "$c"
git log --format='%an <%ae> | %cn <%ce> | %s' -3
python3 -I scripts/check_privacy.py --selftest; echo "selftest rc $?"
python3 -I scripts/check_privacy.py; echo "gate rc $?"
git checkout -q --detach "$HEAD"
echo "restored: $(git rev-parse HEAD) status-entries $(git status --porcelain | wc -l)"
