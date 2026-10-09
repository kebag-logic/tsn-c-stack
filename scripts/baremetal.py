#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build, audit and execute the complete freestanding RV32 minimal port."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
from check_boundary import compile_flags, dependencies

ROOT = Path(__file__).resolve().parents[1]
SYMBOLS = {'memset', 'memcpy', 'ctrl_reentry_assert', 'port_assert_failed',
           '__mulsi3', '__umodsi3', '__udivsi3', '__divsi3', '__modsi3',
           '__ashldi3', '__ashrdi3', '__lshrdi3', '__muldi3', '__udivdi3', '__umoddi3'}


def command(argv, cwd=ROOT):
    result = subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=180)
    if result.returncode:
        raise RuntimeError('command failed: ' + ' '.join(map(str, argv)) + '\n' + result.stdout)
    return result.stdout


def build(work, kind, jobs):
    directory = work / kind.lower()
    command(['cmake', '-S', str(ROOT), '-B', str(directory),
             '-DCMAKE_TOOLCHAIN_FILE=' + str(ROOT / 'cmake/rv32.cmake'),
             '-DCMAKE_BUILD_TYPE=' + kind])
    output = command(['cmake', '--build', str(directory), '-j' + str(jobs)])
    (directory / 'build.log').write_text(output)
    entries = json.loads((directory / 'compile_commands.json').read_text())
    core = [e for e in entries if Path(e['file']).parent == ROOT / 'src']
    if not ({Path(e['file']).name for e in core} == {'adp.c', 'acmp.c', 'maap.c'}):
        raise RuntimeError('freestanding build must compile all three cores')
    flags = compile_flags(core[0])
    compiler = flags[0]
    nm = command([compiler, '-print-prog-name=nm']).strip()
    builtin = Path(command([compiler, '-print-file-name=include']).strip()).resolve()
    allowed_roots = [ROOT / 'include', ROOT / 'examples/rv32/include', builtin]
    objects = {}
    generated_objects = {}
    imports = set()
    for entry in core:
        flags = compile_flags(entry)
        if not (all(flag in flags for flag in ('-march=rv32i', '-mabi=ilp32', '-ffreestanding', '-nostdinc'))):
            raise RuntimeError('missing mandatory RV32 freestanding flags: ' + entry['file'])
        cwd = Path(entry['directory'])
        source = Path(entry['file'])
        for path in dependencies(flags, source, cwd):
            if not (path == source or any(path.is_relative_to(root) for root in allowed_roots)):
                raise RuntimeError('forbidden core dependency: ' + str(path))
        obj = directory / ('CMakeFiles/tsn.dir/src/' + source.name + '.obj')
        symbols = {line.split()[0] for line in command([nm, '-u', '-f', 'posix', str(obj)]).splitlines()}
        if not (symbols <= SYMBOLS):
            raise RuntimeError('forbidden core imports: ' + ', '.join(sorted(symbols - SYMBOLS)))
        imports |= symbols
        objects[source.name] = hashlib.sha256(obj.read_bytes()).hexdigest()
    generated = [e for e in entries if Path(e['file']).name == 'entity_config.c']
    if len(generated) != 4:
        raise RuntimeError('freestanding build must compile all four generated entities')
    for entry in generated:
        source = Path(entry['file'])
        flags = compile_flags(entry)
        if not all(flag in flags for flag in ('-march=rv32i', '-mabi=ilp32', '-ffreestanding', '-nostdinc')):
            raise RuntimeError('missing generated configuration freestanding flags')
        for path in dependencies(flags, source, directory):
            if path != source and path != source.with_suffix('.h') and not any(path.is_relative_to(root) for root in allowed_roots):
                raise RuntimeError('forbidden generated configuration dependency: ' + str(path))
        obj = directory / 'CMakeFiles/entity_examples.dir' / (str(source.relative_to(ROOT)) + '.obj')
        if command([nm, '-u', str(obj)]).strip():
            raise RuntimeError('generated configuration must have no imports')
        generated_objects[source.parent.name] = hashlib.sha256(obj.read_bytes()).hexdigest()
    elf = directory / 'rv32_smoke.elf'
    header = elf.read_bytes()[:52]
    if not (header[:6] == b'\x7fELF\x01\x01'):
        raise RuntimeError('expected little-endian ELF32')
    if not (struct.unpack_from('<H', header, 18)[0] == 243):
        raise RuntimeError('expected RISC-V')
    if not (struct.unpack_from('<I', header, 36)[0] == 0):
        raise RuntimeError('expected RV32I soft-float ABI')
    if command([nm, '-u', str(elf)]).strip():
        raise RuntimeError('unresolved final symbols')
    output = command(['qemu-system-riscv32', '-machine', 'virt', '-nographic', '-bios', 'none',
                      '-kernel', str(elf), '-no-reboot'])
    (directory / 'smoke.log').write_text(output + 'ADP, ACMP and MAAP smoke checks: rc 0\n')
    return {'configuration': kind, 'rc': 0, 'elf_sha256': hashlib.sha256(elf.read_bytes()).hexdigest(),
            'elf_bytes': elf.stat().st_size, 'core_objects': objects, 'core_imports': sorted(imports),
            'generated_objects': generated_objects, 'unresolved_final': [],
            'smoke': 'ADP discovery and backpressure; ACMP restore and rollback; MAAP timers and range bounds; four generated entity round trips'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=Path('build-rv32'))
    parser.add_argument('--jobs', type=int, default=16)
    args = parser.parse_args()
    work = args.work.resolve()
    (work / 'temp').mkdir(parents=True, exist_ok=True)
    os.environ['TMPDIR'] = str(work / 'temp')
    if not shutil.which('qemu-system-riscv32'):
        raise SystemExit('qemu-system-riscv32 is required')
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda kind: build(work, kind, args.jobs), ('Debug', 'Release')))
    (work / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(results, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
