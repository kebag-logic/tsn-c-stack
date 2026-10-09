# SPDX-License-Identifier: MIT
"""The assertion vocabulary used by the core tests."""
import subprocess
from compiler_tokens import raw_tokens

GTEST_VERSION = '1.14.0'
ALLOWED = frozenset(prefix + suffix for prefix in ('EXPECT_', 'ASSERT_')
                    for suffix in ('TRUE', 'FALSE', 'EQ', 'NE', 'LE', 'GE')) | {'EXPECT_EXIT', 'EXPECT_CALL'}


def errors(text):
    return sorted({f'unsupported assertion form: {value}'
                   for kind, value, *_ in raw_tokens(text, 'c++')
                   if kind == 'raw_identifier'
                   and (value.startswith(('EXPECT_', 'ASSERT_'))
                        or value in ('FAIL', 'ADD_FAILURE', 'ADD_FAILURE_AT', 'SUCCEED', 'GTEST_SKIP'))
                   and value not in ALLOWED})


def require_version():
    for package in ('gtest', 'gmock'):
        version = subprocess.check_output(['pkg-config', '--modversion', package], text=True).strip()
        if version != GTEST_VERSION:
            raise RuntimeError(package + ' must be version ' + GTEST_VERSION + ', found ' + version)
