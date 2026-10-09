# SPDX-License-Identifier: MIT
"""The assertion vocabulary used by the core tests."""
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
from compiler_tokens import raw_tokens

GTEST_VERSION = '1.14.0'
ALLOWED = frozenset(prefix + suffix for prefix in ('EXPECT_', 'ASSERT_')
                    for suffix in ('TRUE', 'FALSE', 'EQ', 'NE', 'LE', 'GE')) | {'EXPECT_EXIT', 'EXPECT_CALL'}


def errors(text):
    refused = json.loads(Path(__file__).with_name('assertion-defaults.json').read_text())['refused_macros']
    found = set()
    for kind, value, *_ in raw_tokens(text, 'c++'):
        if kind == 'hashhash':
            found.add('token pasting is forbidden in tests')
        if kind == 'raw_identifier' and value not in ALLOWED and (
                value in refused or value.startswith(('EXPECT_', 'ASSERT_', 'GTEST_'))):
            found.add(f'unsupported assertion form: {value}')
    return sorted(found)


def package_flags(*options):
    flags = iter(shlex.split(subprocess.check_output(
        ['pkg-config', *options, 'gmock', 'gtest'], text=True)))
    result = []
    for flag in flags:
        if flag == '-I':
            path = next(flags, None)
            if not path:
                raise RuntimeError('package include option has no path')
            result.extend(['-isystem', path])
        elif flag.startswith('-I'):
            result.extend(['-isystem', flag[2:]])
        else:
            result.append(flag)
    return result


def refused_macros():
    require_version()
    headers = set()
    for package in ('gtest', 'gmock'):
        include = Path(subprocess.check_output(
            ['pkg-config', '--variable=includedir', package], text=True).strip())
        public = sorted((include / package).glob('*.h'))
        if not public:
            raise RuntimeError('pinned package has no public headers: ' + package)
        headers.update(path.relative_to(include).as_posix() for path in public)
    result = subprocess.run([os.environ.get('CXX', 'g++'), '-std=c++20',
                             *package_flags('--cflags'), '-x', 'c++', '-dM', '-E', '-'],
                            input=''.join('#include <' + name + '>\n' for name in sorted(headers)),
                            text=True, capture_output=True, check=True)
    names = set(re.findall(r'^#define ([A-Za-z_]\w*)\(', result.stdout, re.M))
    public = {name for name in names if not name.endswith('_') and
              (name.startswith(('EXPECT_', 'ASSERT_', 'GTEST_', 'FAIL', 'ADD_FAILURE'))
               or name == 'SUCCEED')}
    if not ALLOWED <= public:
        raise RuntimeError('pinned headers lack an allowed assertion macro')
    return sorted(public - ALLOWED)


def require_version():
    for package in ('gtest', 'gmock'):
        version = subprocess.check_output(['pkg-config', '--modversion', package], text=True).strip()
        if version != GTEST_VERSION:
            raise RuntimeError(package + ' must be version ' + GTEST_VERSION + ', found ' + version)
