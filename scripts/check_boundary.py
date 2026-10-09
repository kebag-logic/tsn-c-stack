#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check compiler dependencies and object symbols at the library boundary."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
C_HEADERS = set('assert complex ctype errno fenv float inttypes iso646 limits locale math stdalign stdarg stdatomic stdbool stddef stdint stdio stdlib stdnoreturn string tgmath uchar wchar wctype'.split())
HEAP = {'malloc', 'calloc', 'realloc', 'free', 'aligned_alloc', 'reallocarray',
        'strdup', 'strndup', 'posix_memalign', 'memalign', 'valloc', 'pvalloc'}
C_SYMBOLS = {'memset', 'memcpy', 'memmove', 'memcmp', '__stack_chk_fail',
             '__assert_fail', '__assert_rtn', 'ctrl_reentry_assert'}


def run(command, cwd):
    return subprocess.check_output(command, cwd=cwd, text=True, stderr=subprocess.STDOUT)


def dependencies(flags, source, cwd):
    output = run([*flags, '-M', '-MT', 'boundary', str(source)], cwd)
    paths = shlex.split(output.replace('\\\n', '').split(':', 1)[1])
    return {(cwd / path).resolve() for path in paths}


def compile_flags(entry):
    argv = entry.get('arguments') or shlex.split(entry['command'])
    flags = []
    i = 0
    while i < len(argv):
        if argv[i] in ('-o', '-MF', '-MT', '-MQ'):
            i += 2
        elif argv[i] in ('-c', '-MD', '-MMD', '-MP') or argv[i] == entry['file']:
            i += 1
        else:
            flags.append(argv[i])
            i += 1
    return flags


def inspect(root, build, compiler, jobs):
    run(['cmake', '-S', str(root), '-B', str(build), '-DTSN_TESTS=OFF',
         '-DCMAKE_BUILD_TYPE=Debug', '-DCMAKE_C_COMPILER=' + compiler], root)
    run(['cmake', '--build', str(build), '-j' + str(jobs)], root)
    entries = json.loads((build / 'compile_commands.json').read_text())
    sources = {Path(e['file']).resolve() for e in entries}
    errors = [f'unbuilt library source: {p.relative_to(root)}'
              for p in (root / 'src').rglob('*.c') if p.resolve() not in sources]
    standard = build / 'standard.c'
    standard.write_text(''.join(f'#include <{h}.h>\n' for h in sorted(C_HEADERS)))
    for entry in entries:
        cwd = Path(entry['directory'])
        flags = compile_flags(entry)
        # Obtain the compiler's standard-header closure without repository search paths.
        system_flags = []
        i = 0
        while i < len(flags):
            if flags[i] in ('-I', '-iquote', '-isystem'):
                i += 2
            elif flags[i].startswith(('-I', '-iquote', '-isystem')):
                i += 1
            else:
                system_flags.append(flags[i])
                i += 1
        allowed = dependencies(system_flags, standard, cwd) - {standard.resolve()}
        source = Path(entry['file']).resolve()
        units = [source, *sorted((root / 'include').rglob('*.h'))]
        for unit in units:
            for path in dependencies(flags, unit, cwd):
                owned = path.is_relative_to((root / 'include').resolve())
                if path != unit and not owned and path not in allowed:
                    errors.append(f'{source.name}: forbidden dependency {path.name}')
        argv = entry.get('arguments') or shlex.split(entry['command'])
        obj = cwd / argv[argv.index('-o') + 1]
        for line in run(['nm', '--undefined-only', '--format=posix', str(obj)], cwd).splitlines():
            symbol = line.split()[0].split('@')[0]
            if symbol in HEAP:
                errors.append(f'{source.name}: dynamic allocation symbol {symbol}')
            elif symbol not in C_SYMBOLS:
                errors.append(f'{source.name}: unsupported external symbol {symbol}')
    return errors


def check(root, work, jobs=16):
    errors = []
    for compiler in ('gcc', 'clang'):
        try:
            errors += [compiler + ': ' + e for e in inspect(root, work / compiler, compiler, jobs)]
        except subprocess.CalledProcessError as error:
            errors.append(compiler + ': compiler boundary examination failed\n' + error.output)
    return errors


def selftest(work, jobs):
    root = work / 'controls'
    (root / 'src').mkdir(parents=True, exist_ok=True)
    (root / 'include').mkdir(exist_ok=True)
    (root / 'CMakeLists.txt').write_text((ROOT / 'CMakeLists.txt').read_text())
    (root / 'include/own.h').write_text('#include <stdint.h>\n')
    (root / 'outside.h').write_text('')
    (root / 'src/acmp.c').write_text('int second(void) { return 0; }\n')
    (root / 'src/maap.c').write_text('int third(void) { return 0; }\n')
    controls = {
        'owned-and-standard': ('#include "own.h"\n#include <stdlib.h>\nuint32_t value(void) { return 1; }', False),
        'standard-digraph': ('%:include <stdint.h>\nuint32_t value(void) { return 1; }', False),
        'outside-hash': ('#include <unistd.h>\nint value(void) { return getpid(); }', True),
        'outside-digraph': ('%:include <unistd.h>\nint value(void) { return getpid(); }', True),
        'outside-trigraph': ('#pragma GCC diagnostic ignored "-Wtrigraphs"\n??=include <unistd.h>\nint value(void) { return getpid(); }', True),
        'outside-relative': ('#include "../outside.h"\nint value(void) { return 1; }', True),
        'outside-spliced': ('#inc\\\nlude <unistd.h>\nint value(void) { return getpid(); }', True),
        'outside-macro': ('#define HEADER <unistd.h>\n#include HEADER\nint value(void) { return getpid(); }', True),
        'heap-direct': ('#include <stdlib.h>\nvoid *value(void) { return malloc(4); }', True),
        'heap-macro': ('#include <stdlib.h>\n#define TSN_GET malloc\nvoid *value(void) { return TSN_GET(4); }', True),
        'heap-pointer': ('#include <stdlib.h>\nvoid *(*const value)(size_t) = malloc;', True),
        'os-symbol': ('extern int getpid(void);\nint value(void) { return getpid(); }', True),
    }
    for name, (source, forbidden) in controls.items():
        (root / 'src/adp.c').write_text(source + '\n')
        # inspect() builds every control before checking dependencies and symbols.
        for compiler in ('gcc', 'clang'):
            errors = inspect(root, work / ('control-' + compiler), compiler, jobs)
            assert bool(errors) == forbidden, (name, compiler, errors)
        print(f'boundary control {name}: compiles; ' + ('refused' if forbidden else 'passes'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selftest', action='store_true')
    parser.add_argument('--work', type=Path, default=Path('build-boundary'))
    parser.add_argument('--jobs', type=int, default=16)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='boundary-', dir=args.work.resolve()) as temporary:
        work = Path(temporary)
        if args.selftest:
            selftest(work, args.jobs)
        errors = check(ROOT, work / 'library', args.jobs)
    print('\n'.join(errors) if errors else 'boundary: compiler dependencies and object symbols pass')
    raise SystemExit(bool(errors))
