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
        if kind == 'raw_identifier' and value in refused:
            found.add(f'unsupported assertion form: {value}')
    return sorted(found)


def package_flags(*options):
    return shlex.split(subprocess.check_output(
        ['pkg-config', *options, 'gmock', 'gtest'], text=True))


def refused_macros():
    require_version()
    result = subprocess.run([os.environ.get('CXX', 'g++'), '-std=c++20',
                             *package_flags('--cflags'), '-x', 'c++', '-dM', '-E', '-'],
                            input='#include <gtest/gtest.h>\n#include <gmock/gmock.h>\n',
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
