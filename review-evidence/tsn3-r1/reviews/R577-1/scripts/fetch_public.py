#!/usr/bin/env python3
"""Fetch public review inputs and hosted job metadata using read-only requests."""
import json
from pathlib import Path
import subprocess

packet=Path(__file__).resolve().parents[1]
scratch=packet/'scratch'; scratch.mkdir(exist_ok=True)
queries={
    'raw-issue3':'repos/kebag-logic/tsn-c-stack/issues/3',
    'issue3-comments-final':'repos/kebag-logic/tsn-c-stack/issues/3/comments',
    'pr19-comments-final':'repos/kebag-logic/tsn-c-stack/issues/19/comments',
    'pr19-reviews':'repos/kebag-logic/tsn-c-stack/pulls/19/reviews',
    'pr19-review-comments':'repos/kebag-logic/tsn-c-stack/pulls/19/comments',
    'pr19':'repos/kebag-logic/tsn-c-stack/pulls/19',
    'pr-jobs-final':'repos/kebag-logic/tsn-c-stack/actions/runs/37964068147/jobs',
    'push-jobs-final':'repos/kebag-logic/tsn-c-stack/actions/runs/37964060914/jobs',
}
for name,url in queries.items():
    raw=subprocess.check_output(['gh','api',url+'?per_page=100'])
    json.loads(raw)
    (scratch/(name+'.json')).write_bytes(raw)
print('Public inputs fetched. Read prior findings only after recording an independent verdict.')
