#!/usr/bin/env python3
"""Compare the recorded PR validation figure with exact-head execution."""
import json
from pathlib import Path
import re
import sys

packet = Path(sys.argv[1])
pr = json.loads((packet / 'scratch/pr18.json').read_text())
gates = json.loads((packet / 'scratch/validate-compatible/gates.json').read_text())
hosted = (packet / 'scratch/hosted-quality.log').read_text()
claim = next(line for line in pr['body'].splitlines() if re.search(r'all \d+ `validate.py` gates', line))
claimed_count = int(re.search(r'all (\d+) `validate.py` gates', claim)[1])
executed = re.findall(r'\b([a-z][a-z-]+): rc 0\s*$', hosted, re.M)
assert pr['head']['sha'] == 'db950cfa959f501932a47d4113733a671f882a83'
assert all(g['rc'] == 0 for g in gates)
assert len(gates) == len({g['gate'] for g in gates}) == 25
assert set(executed) == {g['gate'] for g in gates}
print('head:', pr['head']['sha'])
print('PR URL:', pr['html_url'])
print('PR body updated_at:', pr['updated_at'])
print('PR validation paragraph:', claim)
print('claimed gate count:', claimed_count)
print('completed local gate count:', len(gates))
print('completed hosted gate count:', len(executed))
print('all local return codes zero: true')
print('hosted and local gate-name sets match: true')
print('additional gate introduced by the manager merge: privacy-selftest')
print('finding R561-1-F1:', 'resolved' if claimed_count == len(gates) else 'reproduced: incorrect PR validation figure')
