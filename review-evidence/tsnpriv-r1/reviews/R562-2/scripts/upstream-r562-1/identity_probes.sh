#!/bin/sh
# Synthetic-history probes of scripts/check_privacy.py at the exact head.
# Usage: identity_probes.sh <review-clone> <scratch-dir>   (prints a TSV table)
set -u
SRC=$1; W=$2/idprobe
HEAD=61fb7c9a523b89cb96d493c5baf9f7f866ebed85
LEAK="/ho"; LEAK="${LEAK}me/leak/"  # restricted path built at run time
H="hackerman-kl"; HE="hackerman-kl@kebag-logic.com"
N="hackerman-kl"; NE="161579364+Mister-M-alt@users.noreply.github.com"
G="GitHub"; GE="noreply@github.com"
rm -rf "$W"; git clone -q --no-local "$SRC" "$W"; cd "$W" || exit 2
git checkout -q --detach "$HEAD"
gate() { python3 -I scripts/check_privacy.py > ../gate.out 2>&1; rc=$?; printf '%s\t%s\t%s\n' "$1" "$rc" "$(grep -v '^privacy: exact owner' ../gate.out | sed "s/[0-9a-f]\{40\}/<sha>/g" | tr '\n' ' ')"; }
mk() { # an ae cn ce msg [parents...]
  an=$1 ae=$2 cn=$3 ce=$4 msg=$5; shift 5
  tree=$(git rev-parse HEAD^{tree}); pa=""; for p in "$@"; do pa="$pa -p $p"; done
  printf '%b' "$msg" | env GIT_AUTHOR_NAME="$an" GIT_AUTHOR_EMAIL="$ae" GIT_COMMITTER_NAME="$cn" GIT_COMMITTER_EMAIL="$ce" git commit-tree $tree $pa
}
case_() { name=$1; shift; c=$(mk "$@" "$HEAD"); git checkout -q --detach "$c"; printf "%s\t" "$(git show -s --format="%an <%ae> / %cn <%ce>" HEAD)"; gate "$name"; git checkout -q --detach "$HEAD"; }
printf 'case\trc\toutput\n'
gate "head-as-published"
case_ holder-pair-one-line "$H" "$HE" "$H" "$HE" 'Subject\n'
case_ webflow-pair-one-line "$N" "$NE" "$G" "$GE" 'Subject (#99)\n'
case_ webflow-pair-commit-list-body "$N" "$NE" "$G" "$GE" 'Subject (#99)\n\n* First\n\n* Second\n'
case_ webflow-pair-coauthor-trailer "$N" "$NE" "$G" "$GE" 'Subject (#99)\n\nCo-authored-by: x <x@y.z>\n'
case_ mixed-noreply-author-holder-committer "$N" "$NE" "$H" "$HE" 'Subject\n'
case_ mixed-holder-author-github-committer-rebase-merge "$H" "$HE" "$G" "$GE" 'Subject\n'
case_ foreign-noreply-same-name "$N" "99999999+someone-else@users.noreply.github.com" "$G" "$GE" 'Subject\n'
case_ foreign-noreply-other-name "someone-else" "99999999+someone-else@users.noreply.github.com" "$G" "$GE" 'Subject\n'
case_ same-noreply-other-name "Mister-M-alt" "$NE" "$G" "$GE" 'Subject\n'
case_ noreply-uppercase-variant "$N" "161579364+mister-m-alt@users.noreply.github.com" "$G" "$GE" 'Subject\n'
case_ legacy-noreply-form "$N" "Mister-M-alt@users.noreply.github.com" "$G" "$GE" 'Subject\n'
case_ github-committer-other-email "$N" "$NE" "$G" "web-flow@github.com" 'Subject\n'
case_ reversed-pair "$G" "$GE" "$N" "$NE" 'Subject\n'
case_ noreply-both-roles "$N" "$NE" "$N" "$NE" 'Subject\n'
case_ github-both-roles "$G" "$GE" "$G" "$GE" 'Subject\n'
# Merge commits (two parents): side branch from the base holds one holder-identity commit.
side=$(GIT_AUTHOR_NAME=$H GIT_AUTHOR_EMAIL=$HE GIT_COMMITTER_NAME=$H GIT_COMMITTER_EMAIL=$HE sh -c "printf 'Side\n' | git commit-tree $(git rev-parse HEAD^{tree}) -p 18d737832c376f32660eb21fe2796e0b611507e3")
m=$(mk "$N" "$NE" "$G" "$GE" 'Merge pull request #99 from kebag-logic/side\n\nSide title\n' "$HEAD" "$side"); git checkout -q --detach "$m"; gate merge-webflow-github-default-message; git checkout -q --detach "$HEAD"
m=$(mk "$N" "$NE" "$G" "$GE" 'Merge pull request #99 from kebag-logic/side\n' "$HEAD" "$side"); git checkout -q --detach "$m"; gate merge-webflow-one-line-message; git checkout -q --detach "$HEAD"
fside=$(GIT_AUTHOR_NAME=x GIT_AUTHOR_EMAIL=x@y.z GIT_COMMITTER_NAME=x GIT_COMMITTER_EMAIL=x@y.z sh -c "printf 'Side\n' | git commit-tree $(git rev-parse HEAD^{tree}) -p 18d737832c376f32660eb21fe2796e0b611507e3")
m=$(mk "$N" "$NE" "$G" "$GE" 'Merge pull request #99 from kebag-logic/side\n' "$HEAD" "$fside"); git checkout -q --detach "$m"; gate merge-webflow-one-line-foreign-side-commit; git checkout -q --detach "$HEAD"
# Mailmap: a foreign pair mapped onto the web-flow pair by an untracked .mailmap and log.mailmap.
c=$(mk "someone" "a@b.c" "other" "c@d.e" 'Subject\n' "$HEAD"); git checkout -q --detach "$c"
printf '%s <%s> <a@b.c>\n%s <%s> <c@d.e>\n' "$N" "$NE" "$G" "$GE" > .mailmap; git config log.mailmap true
gate foreign-pair-with-mailmap-to-webflow; rm -f .mailmap; git config --unset log.mailmap; git checkout -q --detach "$HEAD"
# Raw commit header content outside the formatted identity (pre-existing scan scope).
for pair in "holder:$H <$HE>:$H <$HE>" "webflow:$N <$NE>:$G <$GE>"; do
  label=${pair%%:*}; rest=${pair#*:}; a=${rest%%:*}; cm=${rest#*:}
  raw=$(printf 'tree %s\nparent %s\nauthor %s <x%s> 1760000000 +0000\ncommitter %s 1760000000 +0000\nx-extra %s\n\nSubject\n' "$(git rev-parse HEAD^{tree})" "$HEAD" "$a" "$LEAK" "$cm" "$LEAK" | git hash-object -t commit -w --literally --stdin)
  git checkout -q --detach "$raw"; gate "raw-hidden-path-$label"; git cat-file commit "$raw" | grep -c "$LEAK" | sed "s/^/  raw-object-lines-with-path-$label: /"; git checkout -q --detach "$HEAD"
done
python3 -I scripts/check_privacy.py --selftest; echo "selftest rc $?"
python3 -I scripts/check_privacy.py --selftst > ../typo.out 2>&1; echo "misspelled-switch rc $? -> $(tail -1 ../typo.out | sed 's/[0-9]* commits.*/<runs main gate>/')"
