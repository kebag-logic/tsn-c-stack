# SPDX-License-Identifier: MIT
"""Collect assertion message literals by test, including called test helpers."""
import ast
import re
from compiler_tokens import raw_tokens
from assertion_forms import ALLOWED


def tokens(text):
    return [value for kind, value, *_ in raw_tokens(text, 'c++')
            if kind != 'comment' and not value.isspace()]


def instrument(text, markers):
    """Delimit streamed diagnostics in the disposable campaign test sources."""
    lexed = [t for t in raw_tokens(text, 'c++') if t[0] != 'comment' and not t[1].isspace()]
    words = [t[1] for t in lexed]
    closing = pairs(words)
    insertions = []
    for i, word in enumerate(words[:-1]):
        if words[i + 1] != '(' or not re.fullmatch(r'(?:ASSERT|EXPECT)_\w+|FAIL|ADD_FAILURE', word):
            continue
        start = closing[i + 1] + 1
        if start == len(words) or words[start] != '<<':
            continue
        end = start
        while end < len(words) and words[end] != ';':
            end = closing[end] + 1 if end in closing else end + 1
        if end == len(words):
            raise ValueError('unterminated assertion stream')
        for at, marker in ((start, markers[0]), (end, markers[1])):
            insertions.append((lexed[at][2], ' << "\\n' + marker + '\\n" '))
    data = text.encode()
    for at, value in sorted(insertions, reverse=True):
        data = data[:at] + value.encode() + data[at:]
    return data.decode()


def pairs(words):
    stack = []
    ends = {}
    for i, word in enumerate(words):
        if word in ('(', '{', '['):
            stack.append((word, i))
        elif word in (')', '}', ']'):
            if not stack or stack[-1][0] != {')': '(', '}': '{', ']': '['}[word]:
                raise ValueError('unbalanced test source')
            _, start = stack.pop()
            ends[start] = i
    if stack:
        raise ValueError('unbalanced test source')
    return ends


def literal(word):
    if word.startswith('R"'):
        return word[word.index('(') + 1:word.rindex(')')]
    if word.startswith('"'):
        return ast.literal_eval(word)
    return None


def inventory(text):
    words = tokens(text)
    ends = pairs(words)
    tests, helpers = {}, {}
    for i, word in enumerate(words[:-1]):
        if words[i + 1] != '(' or not re.fullmatch(r'\w+', word):
            continue
        close = ends[i + 1]
        if close + 1 >= len(words) or words[close + 1] != '{':
            continue
        body = words[close + 2:ends[close + 1]]
        if word in ('TEST', 'TEST_F', 'TEST_P'):
            if words[i + 3] != ',':
                raise ValueError('unsupported test declaration')
            tests[words[i + 2] + '.' + words[i + 4]] = body
        elif word not in ('if', 'for', 'while', 'switch', 'catch'):
            helpers.setdefault(word, []).append(body)

    def collect(body, visited):
        messages = []
        closing = pairs(body)
        for i, word in enumerate(body[:-1]):
            # A helper may be passed as a callback or constructed as a fixture.
            if word in helpers and word not in visited:
                if len(helpers[word]) != 1:
                    raise ValueError('ambiguous assertion helper: ' + word)
                visited.add(word)
                messages += collect(helpers[word][0], visited)
            if body[i + 1] != '(':
                continue
            if word in ALLOWED:
                at = closing[i + 1] + 1
                while at < len(body) and body[at] == '<<':
                    at += 1
                    value = ''
                    while at < len(body) and literal(body[at]) is not None:
                        value += literal(body[at])
                        at += 1
                    if value and at < len(body) and body[at] in ('<<', ';'):
                        messages.append(value)
                    # Skip one streamed expression, never claim its value as a literal.
                    while at < len(body) and body[at] not in ('<<', ';'):
                        at = closing[at] + 1 if at in closing else at + 1
        return messages

    return {name: collect(body, set()) for name, body in tests.items()}
