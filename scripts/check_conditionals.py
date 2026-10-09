#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compile both sides of every allowed conditional region."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import itertools
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from compiler_tokens import compiler, raw_tokens
from conditional_policy import GUARDS, MACROS, inspect

ROOT = Path(__file__).resolve().parents[1]


def prepare(text, path):
    if 'TSN_BRANCH_' in text:
        raise RuntimeError('conditional marker prefix is reserved for the gate')
    language = 'c++' if path.endswith(('.cpp', '.hpp')) else 'c'
    errors, regions = inspect(raw_tokens(text, language), path)
    if errors:
        raise RuntimeError(path + ': ' + '; '.join(errors))
    changes, expected = [], set()
    data = text.encode()

    def after(row):
        end = data.find(b'\n', row[-1][3])
        return len(data) if end < 0 else end + 1

    for number, region in enumerate(regions):
        if region['guard']:
            continue
        for side in ('true', 'false'):
            marker = 'TSN_BRANCH_' + str(number) + '_' + side
            expected.add(marker)
            pragma = ('.equ ' + marker + ', 0\n' if path.endswith('.S') else
                      '#pragma message("' + marker + '")\n')
            if side == 'true':
                changes.append((after(region['start']), pragma))
            elif region['else']:
                changes.append((after(region['else']), pragma))
            else:
                changes.append((region['end'][0][2], '#else\n' + pragma))
    for offset, value in sorted(changes, reverse=True):
        data = data[:offset] + value.encode() + data[offset:]
    macros = sorted({r['macro'] for r in regions if not r['guard']})
    return data.decode(), expected, macros


def check_coverage(expected, observed):
    missing = expected - observed
    if missing:
        raise RuntimeError('conditional sides never compiled: ' + ', '.join(sorted(missing)))


def compile_file(root, path, work, jobs):
    original = (root / path).read_text()
    source, expected, macros = prepare(original, path)
    directory = work / path.replace('/', '_')
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / Path(path).name
    target.write_text(source)
    flags = ['-Wall', '-Wextra', '-Werror',
             '-I' + str(root / 'include'), '-I' + str(root / 'examples'),
             '-I' + str(root / 'tests'), '-I' + str((root / path).parent)]
    languages = ['c++'] if path.endswith(('.cpp', '.hpp')) else ['c']
    if '__cplusplus' in macros:
        languages = ['c', 'c++']
    values = [m for m in macros if m != '__cplusplus']
    variants = list(itertools.product(languages, itertools.product((False, True), repeat=len(values))))

    def build(item):
        number, (language, defined) = item
        switches = [('-D' + m + '=' + MACROS[m]) if state else '-U' + m
                    for m, state in zip(values, defined)]
        input_file = target
        if target.suffix in ('.h', '.hpp'):
            input_file = directory / (str(number) + ('.cpp' if language == 'c++' else '.c'))
            input_file.write_text('#include "' + target.name + '"\n')
        cc = 'g++' if language == 'c++' else 'gcc'
        extra = []
        if path.startswith('examples/rv32/'):
            cc = shutil.which('riscv64-unknown-elf-gcc') or shutil.which('riscv64-elf-gcc')
            if not cc:
                raise RuntimeError('conditional matrix requires an RV32 compiler')
            builtin = subprocess.check_output([cc, '-print-file-name=include'], text=True).strip()
            extra = ['-march=rv32i', '-mabi=ilp32', '-ffreestanding', '-nostdinc',
                     '-isystem', builtin, '-I' + str(root / 'examples/rv32/include')]
        mode = (['-x', 'assembler-with-cpp'] if path.endswith('.S') else
                ['-x', language, '-std=' + ('c11' if language == 'c' else 'c++20')])
        command = [cc, *mode,
                   *flags, *extra, *switches, '-c', str(input_file), '-o', str(directory / (str(number) + '.o'))]
        result = subprocess.run(command, text=True, capture_output=True, timeout=120)
        (directory / (str(number) + '.log')).write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(path + ': configuration failed: ' + ' '.join(switches) + '\n' + result.stderr)
        seen = set(re.findall(r'#pragma message: (TSN_BRANCH_\d+_(?:true|false))', result.stderr))
        if path.endswith('.S'):
            nm = subprocess.check_output([cc, '-print-prog-name=nm'], text=True).strip()
            symbols = subprocess.check_output([nm, str(directory / (str(number) + '.o'))], text=True)
            seen |= {line.split()[-1] for line in symbols.splitlines() if line.split()} & expected
        return {'language': language, 'defined': dict(zip(values, defined)),
                'rc': 0, 'regions': sorted(seen)}

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        results = list(pool.map(build, enumerate(variants)))
    observed = {marker for result in results for marker in result['regions']}
    check_coverage(expected, observed)
    return {'file': path, 'expected': sorted(expected), 'observed': sorted(observed), 'builds': results}


def selftest(work):
    with tempfile.TemporaryDirectory(dir=work) as name:
        root = Path(name)
        (root / 'src').mkdir()
        source = root / 'src/control.c'
        source.write_text('#ifdef NDEBUG\nint control;\n#else\nlong control;\n#endif\n')
        result = compile_file(root, 'src/control.c', root / 'positive', 2)
        if len(result['observed']) != 2:
            raise RuntimeError('both-side compilation control failed')
        source.write_text('#ifdef NDEBUG\n#ifndef NDEBUG\nint unreachable;\n#endif\n#endif\n')
        try:
            compile_file(root, 'src/control.c', root / 'negative', 2)
        except RuntimeError as error:
            if 'never compiled' not in str(error):
                raise
        else:
            raise RuntimeError('unreachable nested region accepted')
        print('conditional control: compiling nested unreachable region refused')
        (root / 'examples/rv32').mkdir(parents=True)
        assembly = root / 'examples/rv32/control.S'
        assembly.write_text('#ifdef NDEBUG\nnop\n#else\n.word 42\n#endif\n')
        compile_file(root, 'examples/rv32/control.S', root / 'assembly', 2)
        print('conditional control: both assembly sides compiled and found in object symbols')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=Path('build-conditionals'))
    parser.add_argument('--jobs', type=int, default=16)
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    if args.selftest:
        selftest(work)
    standard = (ROOT / 'docs/CODING_STANDARD.md').read_text()
    for macro in list(MACROS) + list(GUARDS.values()):
        if '`' + macro + '`' not in standard:
            raise RuntimeError('conditional allowlist undocumented: ' + macro)
    results = []
    for directory in ('src', 'include', 'tests', 'examples'):
        for path in sorted((ROOT / directory).rglob('*')):
            if path.suffix in ('.c', '.h', '.cpp', '.hpp', '.S'):
                relative = path.relative_to(ROOT).as_posix()
                results.append(compile_file(ROOT, relative, work, args.jobs))
    (work / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    print(f'conditionals: {len(results)} files; ' +
          str(sum(len(r['expected']) for r in results)) + ' region sides compiled')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
