# SPDX-License-Identifier: MIT
"""Read raw token locations from Clang without preprocessing away comments."""
from functools import lru_cache
import os
import re
import shutil
import subprocess


@lru_cache(maxsize=1)
def compiler():
    binary = os.environ.get('TSN_CLANG', shutil.which('clang-18') or 'clang-18')
    result = subprocess.run([binary, '--version'], capture_output=True, text=True, check=True)
    if not re.search(r'clang version 18\.', result.stdout):
        raise RuntimeError('comment lexing requires Clang 18')
    return binary


def logical(text, language='c'):
    if language == 'c':
        table = dict(zip("=/'()!<>-", '#\\^[]|{}~'))
        text = re.sub(r'\?\?([=/\'()!<>-])', lambda m: table[m[1]], text)
    return re.sub(r'\\[ \t]*(?:\r\n|\n|\r)', '', text)


@lru_cache(maxsize=1024)
def raw_tokens(text, language='c'):
    result = subprocess.run(
        [compiler(), '-cc1', '-x', language,
         '-std=' + ('c11' if language == 'c' else 'c++20'), '-dump-raw-tokens', '-'],
        input=text.encode(), capture_output=True, timeout=30)
    dump = result.stderr.decode()
    if result.returncode:
        raise RuntimeError('raw token extraction failed: ' + dump)
    # This parses the compiler's dump envelope, never C or C++ token syntax.
    records = list(re.finditer(
        r'^([a-z_][a-z_0-9]*)\s+\'.*?Loc=<<stdin>:(\d+):(\d+)>[^\n]*\n',
        dump, re.M | re.S))
    cursor = 0
    offsets = [0]
    data = text.encode()
    offsets += [m.end() for m in re.finditer(rb'\r\n|\r|\n', data)]
    starts = []
    for record in records:
        if record.start() != cursor:
            raise RuntimeError('unrecognized raw token dump')
        cursor = record.end()
        row, column = int(record[2]), int(record[3])
        if not 0 < row <= len(offsets):
            raise RuntimeError('invalid raw token location')
        start = offsets[row - 1] + column - 1
        if (not starts and start != 0) or (starts and start <= starts[-1]):
            raise RuntimeError('noncontiguous raw token locations')
        starts.append(start)
    if cursor != len(dump) or (data and not records):
        raise RuntimeError('incomplete raw token dump')
    ends = starts[1:] + [len(data)]
    tokens = []
    for record, start, end in zip(records, starts, ends):
        physical = data[start:end].decode()
        value = (physical if re.match(r'(?:u8|u|U|L)?R"', physical)
                 else logical(physical, language))
        envelope = record[0][len(record[1]):].lstrip()
        if not envelope.startswith("'" + value + "'"):
            raise RuntimeError('raw token spelling disagrees with source locations')
        tokens.append((record[1], value, start, end, int(record[2])))
    return tuple(tokens)


def directives(tokens):
    """Collect directives from compiler tokens at the start of a logical line."""
    result, line = [], []
    for token in tokens:
        kind, value, _, _, _ = token
        if kind == 'unknown' and ('\n' in value or '\r' in value):
            if line and line[0][0] == 'hash':
                result.append(line)
            line = []
        elif kind != 'comment' and not (kind == 'unknown' and value.isspace()):
            line.append(token)
    if line and line[0][0] == 'hash':
        result.append(line)
    return result
